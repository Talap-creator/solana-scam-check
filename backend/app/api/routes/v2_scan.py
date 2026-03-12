from __future__ import annotations

from fastapi import APIRouter, Depends, Header, HTTPException, Query
from sqlalchemy.orm import Session

from ...dependencies import get_repository, settings
from ...db import get_db
from ...models import TokenBehaviourSnapshot, TokenFeatureSnapshot, User
from ...scoring import TokenScoringPipeline
from ...scoring.schemas import BehaviourAnalysisResult, ScanTokenV2Request, TokenScanV2Response
from ...services.analyzer import is_valid_solana_address
from ...services.auth import decode_access_token, get_user_by_id
from ...services.plan_limits import daily_scan_limit_for_user, token_scans_today
from ...services.scan_tracking import track_token_scan
from ...services.solana_rpc import SolanaRpcError


router = APIRouter(prefix="/v2/scan", tags=["scan-v2"])

pipeline = TokenScoringPipeline()


def _map_behaviour_analysis_payload(report) -> BehaviourAnalysisResult:
    source = report.behaviour_analysis_v2
    if source is None:
        raise HTTPException(status_code=404, detail="Behaviour analysis is not available for this token.")

    return BehaviourAnalysisResult(
        summary=source.summary,
        overall_behaviour_risk=source.overall_behaviour_risk,
        confidence=source.confidence,
        score=source.score,
        modules={
            key: {
                "status": module.status,
                "severity": module.severity,
                "score": module.score,
                "summary": module.summary,
                "details": module.details,
                "evidence": module.evidence.metrics,
                "confidence": module.confidence,
            }
            for key, module in source.modules.items()
        },
        confidence_breakdown=source.confidence_breakdown.model_dump(mode="json"),
        version=source.version,
        debug=source.debug,
    )


@router.post("/token", response_model=TokenScanV2Response)
async def scan_token_v2(
    payload: ScanTokenV2Request,
    db: Session = Depends(get_db),
    authorization: str | None = Header(default=None),
) -> TokenScanV2Response:
    if payload.chain != "solana":
        raise HTTPException(status_code=400, detail="Only Solana chain is supported in v2 right now.")
    if not is_valid_solana_address(payload.token_address):
        raise HTTPException(status_code=400, detail="Invalid Solana token mint address.")
    user: User | None = None
    if authorization and authorization.lower().startswith("bearer "):
        token = authorization.split(" ", 1)[1].strip()
        if token:
            try:
                user_id = decode_access_token(token)
                user = get_user_by_id(db, user_id)
            except HTTPException:
                user = None

    if user is not None:
        used_today = token_scans_today(db, user)
        daily_limit, _ = daily_scan_limit_for_user(user, settings)
        if used_today >= daily_limit:
            raise HTTPException(
                status_code=429,
                detail=(
                    f"Daily scan limit reached for plan '{user.plan}'. "
                    f"Used {used_today}/{daily_limit} token scans today (UTC)."
                ),
            )

    try:
        report = get_repository().create_report("token", payload.token_address)
    except SolanaRpcError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    result = pipeline.run(report=report)
    response = result.response

    snapshot = TokenFeatureSnapshot(
        token_address=result.features.token_address,
        feature_json=result.features.model_dump(mode="json"),
        rule_score=response.rule_score,
        ml_probability=response.ml_probability,
        final_score=response.score,
        feature_version=response.feature_metadata["feature_version"],
        model_version=response.model.version,
    )
    db.add(snapshot)
    if report.behaviour_analysis_v2 is not None:
        developer_cluster_module = report.behaviour_analysis_v2.modules.get("developer_cluster")
        early_buyers_module = report.behaviour_analysis_v2.modules.get("early_buyers")
        insider_selling_module = report.behaviour_analysis_v2.modules.get("insider_selling")
        liquidity_management_module = report.behaviour_analysis_v2.modules.get("liquidity_management")
        behaviour_snapshot = TokenBehaviourSnapshot(
            token_address=result.features.token_address,
            developer_cluster_json=developer_cluster_module.model_dump(mode="json") if developer_cluster_module is not None else {},
            early_buyers_json=early_buyers_module.model_dump(mode="json") if early_buyers_module is not None else {},
            insider_selling_json=insider_selling_module.model_dump(mode="json") if insider_selling_module is not None else {},
            liquidity_management_json=liquidity_management_module.model_dump(mode="json") if liquidity_management_module is not None else {},
            confidence_breakdown_json=report.behaviour_analysis_v2.confidence_breakdown.model_dump(mode="json"),
            behaviour_risk_score=report.behaviour_analysis_v2.score,
            behaviour_confidence=report.behaviour_analysis_v2.confidence,
            feature_version=report.behaviour_analysis_v2.version,
        )
        db.add(behaviour_snapshot)
    db.commit()

    if user is not None:
        track_token_scan(db, user, report)

    return response


@router.get("/token/{token_address}/behaviour", response_model=BehaviourAnalysisResult)
async def scan_token_behaviour_v2(
    token_address: str,
    debug: bool = Query(default=False),
) -> BehaviourAnalysisResult:
    if not is_valid_solana_address(token_address):
        raise HTTPException(status_code=400, detail="Invalid Solana token mint address.")
    try:
        report = get_repository().create_report("token", token_address)
    except SolanaRpcError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
    payload = _map_behaviour_analysis_payload(report).model_dump(mode="json")
    if not debug:
        payload["debug"] = None
    return BehaviourAnalysisResult.model_validate(payload)
