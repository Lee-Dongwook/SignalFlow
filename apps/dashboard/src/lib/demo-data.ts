import type { DLQEventDetail, DLQEventSummary } from "@/lib/api";

export const demoEvent: DLQEventDetail = {
  event_id: "demo-order-2026-081",
  error_message:
    "필수 필드 'customer_email'이 누락되어 주문 이벤트가 격리되었습니다.",
  reason: "missing_required_value",
  confidence: 0.96,
  approval_status: "pending",
  raw_payload: {
    order_id: "ORD-20260830-081",
    customer_id: "CUS-2048",
    customer_email: null,
    amount: 89000,
    currency: "KRW",
  },
  changes: [
    {
      field: "customer_email",
      before: null,
      after: "minji.kim@example.com",
      reason: "고객 프로필의 검증된 이메일로 보완",
    },
  ],
  corrected_payload: {
    order_id: "ORD-20260830-081",
    customer_id: "CUS-2048",
    customer_email: "minji.kim@example.com",
    amount: 89000,
    currency: "KRW",
  },
  validation_result: { status: "valid", errors: [] },
  audit_logs: [
    "14:30:02 · DLQ에 주문 이벤트가 격리되었습니다.",
    "14:30:04 · AI가 고객 프로필을 기준으로 복구안을 생성했습니다.",
    "14:30:06 · Pydantic 스키마 검증을 통과했습니다.",
  ],
  rationale:
    "customer_id CUS-2048의 검증된 프로필 이메일과 주문 컨텍스트가 일치합니다. 누락된 필드만 보완하므로 데이터 변경 위험이 낮습니다.",
  risk_reason:
    "이메일 값은 프로필 스냅샷에서 가져온 값입니다. 실제 운영에서는 개인정보 접근 권한과 최신성 정책을 함께 확인해야 합니다.",
};

export function demoSummary(
  event: DLQEventDetail,
  analysisStatus = "ready",
): DLQEventSummary {
  return {
    event_id: event.event_id,
    error_message: event.error_message,
    reason: event.reason,
    confidence: event.confidence,
    validation_status: event.validation_result.status,
    approval_status: event.approval_status,
    analysis_status: analysisStatus,
    updated_at: "2026-08-30T14:30:06+09:00",
  };
}
