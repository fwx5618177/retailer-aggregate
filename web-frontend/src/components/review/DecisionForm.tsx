import { useState } from "react";
import { MatchType } from "@/api/types";
import type { ReviewDecisionRequest } from "@/api/types";
import { MATCH_TYPE_LABELS } from "@/utils/constants";
import { clsx } from "clsx";

interface DecisionFormProps {
  tiktokItemId: string;
  shopeeItemId: string;
  currentMatchType: MatchType;
  onSubmit: (
    tiktokItemId: string,
    shopeeItemId: string,
    request: ReviewDecisionRequest,
  ) => void;
  isSubmitting?: boolean;
}

type Decision = "accept" | "reject" | "change_type";

export function DecisionForm({
  tiktokItemId,
  shopeeItemId,
  currentMatchType,
  onSubmit,
  isSubmitting = false,
}: DecisionFormProps) {
  const [decision, setDecision] = useState<Decision | null>(null);
  const [newMatchType, setNewMatchType] = useState<MatchType>(
    currentMatchType,
  );
  const [comment, setComment] = useState("");

  const handleSubmit = () => {
    if (!decision) return;

    const request: ReviewDecisionRequest = {
      decision,
      comment: comment.trim() || undefined,
    };

    if (decision === "change_type") {
      request.new_match_type = newMatchType;
    }

    onSubmit(tiktokItemId, shopeeItemId, request);

    // Reset
    setDecision(null);
    setComment("");
  };

  return (
    <div className="space-y-4 rounded-xl border border-slate-200 bg-slate-50 p-4">
      <p className="text-sm font-semibold text-slate-700">Review Decision</p>

      {/* Decision Radio Buttons */}
      <div className="flex flex-wrap gap-3">
        <button
          type="button"
          onClick={() => setDecision("accept")}
          className={clsx(
            "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
            decision === "accept"
              ? "border-emerald-300 bg-emerald-50 text-emerald-700"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
          )}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M5 13l4 4L19 7"
            />
          </svg>
          Accept
        </button>

        <button
          type="button"
          onClick={() => setDecision("reject")}
          className={clsx(
            "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
            decision === "reject"
              ? "border-rose-300 bg-rose-50 text-rose-700"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
          )}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
          Reject
        </button>

        <button
          type="button"
          onClick={() => setDecision("change_type")}
          className={clsx(
            "flex items-center gap-2 rounded-lg border px-4 py-2 text-sm font-medium transition-colors",
            decision === "change_type"
              ? "border-indigo-300 bg-indigo-50 text-indigo-700"
              : "border-slate-200 bg-white text-slate-600 hover:bg-slate-50",
          )}
        >
          <svg
            className="h-4 w-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5"
            />
          </svg>
          Change Type
        </button>
      </div>

      {/* Match Type Dropdown (when Change Type selected) */}
      {decision === "change_type" && (
        <div className="max-w-xs">
          <label className="mb-1 block text-xs font-medium text-slate-600">
            New Match Type
          </label>
          <select
            className="select-field"
            value={newMatchType}
            onChange={(e) => setNewMatchType(e.target.value as MatchType)}
          >
            {Object.entries(MATCH_TYPE_LABELS)
              .filter(([key]) => key !== "no_match")
              .map(([value, label]) => (
                <option key={value} value={value}>
                  {label}
                </option>
              ))}
          </select>
        </div>
      )}

      {/* Comment */}
      <div>
        <label className="mb-1 block text-xs font-medium text-slate-600">
          Comment (optional)
        </label>
        <textarea
          className="input-field min-h-[80px] resize-y"
          placeholder="Add a note about your decision..."
          value={comment}
          onChange={(e) => setComment(e.target.value)}
        />
      </div>

      {/* Submit */}
      <div className="flex items-center gap-3">
        <button
          onClick={handleSubmit}
          disabled={!decision || isSubmitting}
          className={clsx(
            "btn-primary",
            (!decision || isSubmitting) && "opacity-50 cursor-not-allowed",
          )}
        >
          {isSubmitting ? (
            <>
              <svg
                className="mr-2 h-4 w-4 animate-spin"
                fill="none"
                viewBox="0 0 24 24"
              >
                <circle
                  className="opacity-25"
                  cx="12"
                  cy="12"
                  r="10"
                  stroke="currentColor"
                  strokeWidth="4"
                />
                <path
                  className="opacity-75"
                  fill="currentColor"
                  d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4z"
                />
              </svg>
              Submitting...
            </>
          ) : (
            "Submit Decision"
          )}
        </button>
        {decision && (
          <button
            onClick={() => {
              setDecision(null);
              setComment("");
            }}
            className="text-sm text-slate-500 hover:text-slate-700"
          >
            Cancel
          </button>
        )}
      </div>
    </div>
  );
}
