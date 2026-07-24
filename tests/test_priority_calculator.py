import sys
from pathlib import Path

# Add project root to sys.path
root_dir = Path(__file__).resolve().parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))

from ai.signal import (
    LaneName,
    DecisionReason,
    PriorityBreakdown,
    PriorityScore,
    PriorityResult,
    SignalDecision,
    PriorityCalculator,
)
from ai.analytics.analytics_exporter import LaneStatistics


def test_priority_calculator():
    print("=== Running PriorityCalculator Unit Test ===")

    # 1. Setup mock LaneStatistics for 4 lanes
    mock_stats = {
        "North": LaneStatistics(
            lane_name="North",
            live_count=10,
            pce_score=15.0,
            stopped_count=5,
            total_queue_time_sec=30.0,
            max_queue_time_sec=12.0,
            avg_motion_px_sec=5.0,
            congestion_index=25.0,
            density="HIGH",
            historical_count=50,
        ),
        "South": LaneStatistics(
            lane_name="South",
            live_count=2,
            pce_score=2.0,
            stopped_count=0,
            total_queue_time_sec=0.0,
            max_queue_time_sec=0.0,
            avg_motion_px_sec=40.0,
            congestion_index=2.0,
            density="LOW",
            historical_count=10,
        ),
        "East": LaneStatistics(
            lane_name="East",
            live_count=6,
            pce_score=7.5,
            stopped_count=2,
            total_queue_time_sec=10.0,
            max_queue_time_sec=5.0,
            avg_motion_px_sec=15.0,
            congestion_index=11.5,
            density="MEDIUM",
            historical_count=25,
        ),
        "West": LaneStatistics(
            lane_name="West",
            live_count=4,
            pce_score=4.0,
            stopped_count=1,
            total_queue_time_sec=5.0,
            max_queue_time_sec=3.0,
            avg_motion_px_sec=20.0,
            congestion_index=6.0,
            density="LOW",
            historical_count=18,
        ),
    }

    # 2. Instantiate PriorityCalculator with default weights (0.45, 0.35, 0.20)
    calc = PriorityCalculator(weights={"pce": 0.45, "queue": 0.35, "congestion": 0.20})
    result: PriorityResult = calc.calculate(mock_stats)

    # 3. Assertions
    assert isinstance(result, PriorityResult)
    assert len(result.scores) == 4

    # Top lane should be North
    top = result.highest_priority
    assert top is not None
    assert top.lane == LaneName.NORTH
    assert top.rank == 1

    # Verify score formula: (0.45 * 15.0) + (0.35 * 30.0) + (0.20 * 25.0) = 6.75 + 10.5 + 5.0 = 22.25
    expected_north_score = round(0.45 * 15.0 + 0.35 * 30.0 + 0.20 * 25.0, 2)
    assert top.score == expected_north_score, f"Expected {expected_north_score}, got {top.score}"

    # Verify ranking order: North (1), East (2), West (3), South (4)
    assert result.scores[0].lane == LaneName.NORTH
    assert result.scores[1].lane == LaneName.EAST
    assert result.scores[2].lane == LaneName.WEST
    assert result.scores[3].lane == LaneName.SOUTH

    print("✔ Priority scores computed and ranked correctly:")
    for score in result.scores:
        print(f"  Rank #{score.rank}: Lane '{score.lane.value}' -> Total Score: {score.score} (PCE: {score.breakdown.pce}, Queue: {score.breakdown.queue}, Congestion: {score.breakdown.congestion})")

    # 4. Verify JSON dict export
    dict_payload = result.to_dict()
    assert dict_payload["highest_priority"]["lane"] == "North"
    print("✔ PriorityResult dict payload exported successfully!")

    # 5. Verify SignalDecision creation using LaneName and DecisionReason
    decision = SignalDecision(
        green_lane=top.lane,
        green_duration_sec=35,
        yellow_duration_sec=3,
        red_lanes=[s.lane for s in result.scores[1:]],
        priority_score=top.score,
        reason=DecisionReason.NORMAL,
        reason_details="Highest PCE + Queue Score",
    )
    print("\n" + str(decision))
    assert decision.to_dict()["green_lane"] == "North"
    print("✔ SignalDecision test passed successfully!")


if __name__ == "__main__":
    test_priority_calculator()
