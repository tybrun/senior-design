# Test Plan and Results
## Test Summary Table
ID	  |Test Name | Classification  | Result  |	Notes  |
----  |----      | ----            | ----    | ----    |
GS1	  |ATO Posture Limits Enforced           |	Boundary / Blackbox / Functional / Integration  |	Pass  |   Posture limit correctly enforced
GS2	  |Initiative Bidding Bonus              | Normal / Whitebox / Functional / Unit            |	Pass  | 	Bidding bonus applies correctly
GS3	  |Intel Roll Advantage / Normal         | Boundary / Blackbox / Functional / Integration   |	Pass  | 	Verified at both boundary values (hand size 0 and 4+)
CA4	  |Squadron Activation Token Placement   | Abnormal / Blackbox / Functional / Integration   | Pass  | 	Fighter band-1 restriction enforced, IAMD airbase placement enforced
CA5	  |Token Identity Hidden Until Acquired  |	Normal / Blackbox / Functional / Integration    | Pass  | 	Stealth token acquisition requirement verified
TM6	  |MAS Action Limits Across Tokens       |	Normal / Blackbox / Functional / Integration    | Pass  | 	Actions correctly tracked globally per turn
TM7	  |Shooting Requires Acquisition         |	Boundary / Blackbox / Functional / Integration  | Pass  | 	Winchester flag set correctly after last munition is used
TM8	  |Return to Base and Relaunch Rules     |	Normal / Blackbox / Functional / Integration    | Pass  | 	Return-to-base triggers correctly on next-turn start phase
TM9  	|IAMD Intercept Logic                  |	Boundary / Blackbox / Functional / Integration  | Pass  | 	IAMD reveal-on-shoot correctly reveals token
ES10  |	Endgame Victory Point Calculation    |	Normal / Blackbox / Functional / Integration    | Pass  | 	Attrition and Interdiction scoring paths both verified
