"""
Tenacious Conversion Engine — ICP Classifier with Abstention
Classifies prospects into Tenacious ICP segments with confidence scoring.
Abstains (sends exploratory email) when confidence < threshold.
"""

from typing import Optional
import structlog

log = structlog.get_logger()

ABSTENTION_THRESHOLD = 0.65
SEGMENT_4_AI_MATURITY_MINIMUM = 2  # Segment 4 only for AI maturity >= 2


class ICPClassifier:
    """
    Classifies Tenacious ICP prospects into segments 1-4 with confidence.
    Abstains if confidence below threshold — sends exploratory email instead.
    This prevents segment misclassification failure mode (highest-ROI probe target).
    """

    def classify(self, hiring_brief: dict) -> dict:
        """
        Classify prospect into primary ICP segment.
        Returns: {primary_segment, secondary_segment, confidence, rationale, abstain}
        """
        signals = hiring_brief.get("signals", {})
        funding = signals.get("funding_event", {})
        jobs = signals.get("job_post_velocity", {})
        layoffs = signals.get("layoff_event", {})
        leadership = signals.get("leadership_change", {})
        ai_maturity = signals.get("ai_maturity", {})

        scores = {}

        # --- SEGMENT 1: Recently-funded Series A/B ---
        seg1_score = 0.0
        seg1_reasons = []
        if funding.get("present") and funding.get("within_180_day_window"):
            round_type = funding.get("round_type", "").lower()
            if "series a" in round_type or "series b" in round_type:
                seg1_score += 0.70
                seg1_reasons.append(f"{funding['round_type']} in last 180 days")
            elif "seed" in round_type:
                seg1_score += 0.40
                seg1_reasons.append("Seed round (partial Segment 1 match)")

        job_count = jobs.get("total_open_roles", 0)
        if job_count >= 5:
            seg1_score += 0.20
            seg1_reasons.append(f"{job_count} open roles — hiring velocity")
        elif job_count >= 2:
            seg1_score += 0.10

        # Discount if layoff present (post-layoff = Segment 2 signal)
        if layoffs.get("present"):
            seg1_score *= 0.40
            seg1_reasons.append("DISCOUNTED: Layoff signal present — not a growth play")

        scores["segment_1"] = {
            "score": min(1.0, seg1_score),
            "reasons": seg1_reasons,
        }

        # --- SEGMENT 2: Mid-market restructuring ---
        seg2_score = 0.0
        seg2_reasons = []
        if layoffs.get("present"):
            seg2_score += 0.70
            seg2_reasons.append("Layoff event in last 120 days — cost pressure signal")
        employee_count = hiring_brief.get("prospect", {}).get("employee_count", 0)
        if 200 <= employee_count <= 2000:
            seg2_score += 0.20
            seg2_reasons.append(f"Employee count {employee_count} in mid-market band")
        scores["segment_2"] = {
            "score": min(1.0, seg2_score),
            "reasons": seg2_reasons,
        }

        # --- SEGMENT 3: Engineering leadership transition ---
        seg3_score = 0.0
        seg3_reasons = []
        if leadership.get("present"):
            seg3_score += 0.90
            seg3_reasons.append("New CTO or VP Engineering in last 90 days")
        scores["segment_3"] = {
            "score": min(1.0, seg3_score),
            "reasons": seg3_reasons,
        }

        # --- SEGMENT 4: Specialized capability gap ---
        seg4_score = 0.0
        seg4_reasons = []
        ai_score = ai_maturity.get("score", 0)
        ai_conf = ai_maturity.get("confidence", 0)
        if ai_score >= SEGMENT_4_AI_MATURITY_MINIMUM:
            seg4_score += 0.60
            seg4_reasons.append(f"AI maturity score {ai_score}/3 (≥ 2 threshold)")
            if ai_conf >= 0.80:
                seg4_score += 0.20
                seg4_reasons.append("High confidence AI maturity signal")
        else:
            seg4_reasons.append(f"AI maturity score {ai_score}/3 — below Segment 4 minimum of 2. Do NOT pitch Segment 4.")
        scores["segment_4"] = {
            "score": min(1.0, seg4_score),
            "reasons": seg4_reasons,
        }

        # --- FIND PRIMARY SEGMENT ---
        primary_segment = max(scores, key=lambda k: scores[k]["score"])
        primary_score = scores[primary_segment]["score"]

        # Abstention: if primary confidence below threshold, send exploratory
        if primary_score < ABSTENTION_THRESHOLD:
            log.info("icp_classifier_abstaining",
                     primary_segment=primary_segment,
                     confidence=primary_score,
                     threshold=ABSTENTION_THRESHOLD)
            return {
                "primary_segment": "exploratory",
                "original_best_segment": primary_segment,
                "confidence": primary_score,
                "abstained": True,
                "abstention_reason": f"Best segment confidence {primary_score:.2f} below threshold {ABSTENTION_THRESHOLD}",
                "rationale": f"Insufficient signal for segment-specific pitch. Sending exploratory email.",
                "all_scores": scores,
            }

        # Secondary segment (second highest, if score > 0.30)
        sorted_segments = sorted(scores.items(), key=lambda x: x[1]["score"], reverse=True)
        secondary_segment = None
        if len(sorted_segments) > 1 and sorted_segments[1][1]["score"] > 0.30:
            secondary_segment = sorted_segments[1][0]

        # Edge case: post-layoff company that also recently raised (Seg 2 + Seg 1 conflict)
        # Challenge instruction: "a post-layoff company that also recently raised funding"
        # Resolution: classify as Segment 2 (restructuring) with Segment 1 overlay
        seg1_score_val = scores["segment_1"]["score"]
        seg2_score_val = scores["segment_2"]["score"]
        if seg1_score_val > 0.30 and seg2_score_val > 0.30:
            log.info("icp_classifier_seg1_seg2_conflict",
                     seg1=seg1_score_val, seg2=seg2_score_val,
                     resolution="Segment 2 primary (layoff signal dominates), Segment 1 secondary")
            # Layoff signal dominates — cost restructuring is the primary pitch
            # Segment 1 (growth) language would be wrong for a recently-laid-off company
            primary_segment = "segment_2" if seg2_score_val >= seg1_score_val else "segment_1"
            secondary_segment = "segment_1" if primary_segment == "segment_2" else "segment_2"

        return {
            "primary_segment": primary_segment,
            "secondary_segment": secondary_segment,
            "confidence": primary_score,
            "abstained": False,
            "rationale": " | ".join(scores[primary_segment]["reasons"]),
            "all_scores": scores,
        }
