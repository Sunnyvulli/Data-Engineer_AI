# Astronomy stage-two protocol after a feasibility failure

Fixed October 18, 2026 before inspecting outcomes for the remaining shard objects. The originally selected first 5,000 objects contained zero class-64 events, so rare-event AP and recall cannot be estimated on that sample. That result will be retained, not replaced or assigned a fabricated score.

The first test shard has 32,926 object IDs, counted using the object_id column only. The next evaluation uses **all previously unevaluated objects in this shard with object_id > 53125**, excluding the shard's final object conservatively in case it continues into another file. No selection by class or model score is allowed. All previously evaluated first-5,000 IDs remain excluded.

Use the same frozen three-day forest, same features, same 5% candidate budget, and same 300 object-bootstrap replicates as the original protocol. No refitting, threshold tuning, or target-label-based subset choice. Report the full evaluated class count and wide uncertainty if rare events are sparse. This is an adaptive second stage after a documented feasibility failure, not the original preregistered test or a claim of independent real-survey validation. Simulation and selection limitations remain.
