This is actually a very productive outcome. Looking at the three versions, I'd summarize it like this:

What we learned
v1 (50% rainfall reduction)

Essentially no effect.

Yield gap ≈ 0%
Tr/TrPot ≈ 1.0


Interpretation:

The Story County soil profile buffered the reduction completely.

So v1 is too weak.

v2 (85% rainfall reduction / complete reproductive rainfall removal)
Early Recovery:
Yield = 13.58 t/ha
Yield gap = 7.1%
Tr/TrPot = 0.974

Dual Stress:
Yield = 11.08 t/ha
Yield gap = 24.0%
Tr/TrPot = 0.862


Interpretation:

A meaningful response finally appeared.
Early recovery remained relatively resilient.
Dual stress substantially reduced transpiration and yield.
Late stress still remained surprisingly weak.

This was the first version with a real signal.

v3 (strongest treatment)
Early Recovery:
Yield = 11.85
Yield gap = 18.9%

Late Stress:
Yield = 13.87
Yield gap = 6.0%

Dual Stress:
Yield = 3.69
Yield gap = 36.5%


and

Dual Stress
Mean Wr = 122
Mean Tr/TrPot = 0.851


This is the first version where the treatment is clearly imposing severe stress.

The interesting scientific result

Look at:

Experiment	Yield Gap (%)Early Recovery v3	18.9
Late Stress v3	6.0
Dual Stress v3	36.5

This is not reproducing your observational paper.

Your observational study found:

Dual Stress
↓
largest losses

Late Stress Only
↓
substantial losses

Early Recovery
↓
small or negligible losses


GeoAquaCrop v3 instead gives:

Dual Stress
↓
largest losses

Early Recovery
↓
second largest losses

Late Stress
↓
smallest losses


This discrepancy is scientifically valuable.

My interpretation

The current experiment is:

manipulating rainfall

But your observational paper is really about:

realized drought trajectories

Those are not equivalent.

For example:

Early Recovery

In the model:

85% rainfall reduction
throughout the entire vegetative period


That may be much more severe than the observed Cell B years in your manuscript.

Late Stress

Because of:

Massive stored soil water


the crop still enters reproduction with large reserves.

Thus:

No rainfall
≠
Immediate agricultural drought

What I would do next

I would not build more versions.

I would move to:

13_compare_versions.py

Compare:

v1
v2
v3


for:

Yield
Yield gap
Wr
Tr/TrPot

and determine:

Which treatment design best resembles the observational drought trajectories?

My guess from the current results:

Best candidate
Early Recovery v2
Dual Stress v2


already look reasonable.

Needs redesign
Late Stress


because the soil-water reservoir continues buffering stress.

Most important question now

Before proceeding, I would ask:

Is your goal to reproduce the observational ranking of:

Dual Stress > Late Stress > Early Recovery


or

Is your goal to understand why the model does not reproduce it?

Those are two different scientific directions.

Honestly, the second question may be the more interesting one if you're thinking about a future modeling paper. The current experiments are already revealing that soil-water storage can strongly modulate the expression of meteorological drought, which is very closely related to the SPEI vs SSMI story in your manuscript.

These results are actually quite informative, and I think you've reached the point where you can start framing a scientific hypothesis rather than just testing code.

What stands out immediately
Early Recovery
Version	Yield (t/ha)	Yield Gap (%)	Mean Tr/TrPotv1	14.72	0.25	1.000
v2	13.58	7.09	0.974
v3	11.85	18.89	0.947

As drought intensity increases:

Precipitation ↓
↓
Wr ↓
↓
Tr/TrPot ↓
↓
Yield ↓


But even under v3 the crop still retains:

80.4% of control yield


This is quite consistent with your observational early recovery result.

Late Stress
Version	Yield Gap (%)v1	0.34
v2	0.56
v3	6.02

This is the surprising result.

Even when you removed:

100% reproductive rainfall


(v2)

yield barely changed.

Only when you reduced antecedent moisture (v3) did the crop start responding.

This suggests:

Reproductive rainfall itself is less important than the amount of water carried into reproduction through the soil profile.

That is a very interesting mechanistic insight.

Dual Stress
Version	Yield Gap (%)v1	0.19
v2	23.99
v3	36.51

This behaves exactly as expected.

As soil-water availability declines:

Wr ↓
↓
Tr/TrPot ↓
↓
Yield ↓


Dual stress generates the strongest response.

What I would do next

I would not create more versions.

Instead build:

13_compare_versions.py

to visualize:

v1
v2
v3


for each trajectory.

I would generate:

Yield Gap
yield_gap_pct


vs version.

Mean Wr

vs version.

Mean Tr/TrPot

vs version.

Then ask:

Which version best represents a realistic drought trajectory?

New scientific hypothesis emerging

Based on your current results, the paper-supporting hypothesis is evolving into:

Crop recovery depends on whether sufficient root-zone water storage remains available to sustain transpiration through the reproductive period.

This is actually closer to your manuscript than:

Rainfall returned.

GeoAquaCrop is suggesting:

Rainfall
≠
Root-zone water

Root-zone water
→
Transpiration
→
Yield


which is very much aligned with the SSMI interpretation.

I think your next script should be
13_compare_versions.py

Purpose:

Compare for each trajectory:

Yield gap
Seasonal transpiration
Mean Wr
Mean Tr/TrPot


across:

v1
v2
v3


That will tell us whether:

v3 is overly severe,
v1 is too weak,
v2 is the most realistic representation.

And that decision is important before scaling to:

Illinois
Minnesota
Nebraska


because you want to scale using the best-performing treatment design, not keep redesigning treatments after you've added more locations.
These results are actually very useful because they tell us which treatment design is worth pursuing.

What the version comparison shows
Early Recovery
Version	Yield (t/ha)	Yield Gap (%)	Mean Wr	Mean Tr/TrPotv1	14.72	0.3	196.8	1.000
v2	13.58	7.1	179.4	0.974
v3	11.85	18.9	177.9	0.947

This is behaving exactly as expected.

More drought intensity:

Rainfall ↓
↓
Wr ↓
↓
Tr/TrPot ↓
↓
Yield ↓


This is a nice controlled response.

Late Stress
Version	Yield (t/ha)	Yield Gap (%)	Mean Wr	Mean Tr/TrPotv1	14.72	0.3	214.0	1.000
v2	14.68	0.6	190.5	0.995
v3	13.87	6.0	185.5	0.921

This is the most interesting result.

It tells us:

Story County enters reproduction with enough stored soil water that removing rainfall alone is not enough to create severe late-season stress.

That is exactly why:

v1 ≈ control
v2 ≈ control


and only:

v3


starts producing a substantial response.

Dual Stress
Version	Yield (t/ha)	Yield Gap (%)	Mean Wr	Mean Tr/TrPotv1	14.73	0.2	192.6	1.000
v2	11.08	24.0	196.7	0.862
v3	3.69	36.5	122.2	0.851

This is behaving exactly as expected.

v3 is probably approaching an extreme stress scenario.

Scientific interpretation

The most important outcome so far is:

Early Recovery v2/v3

You have:

Wr remains relatively high
↓
Tr/TrPot remains high
↓
Yield recovery remains substantial


This is very similar to the mechanism implied by your manuscript:

root-zone water recovery supports crop recovery.

In contrast:

Dual Stress
Wr declines
↓
Tr/TrPot declines
↓
Yield collapses


which is also consistent with the observational results.

What I would do next

Instead of adding more versions, I would create:

15_compare_trajectorys.py

Purpose:

Compare the best-performing versions:

control_2015

early_recovery_2015_v2
or
early_recovery_2015_v3

late_stress_2015_v3

dual_stress_2015_v2
or
dual_stress_2015_v3


on a single set of plots.

That moves us from:

Which version works?


to

What does the final drought-timing experiment show?

My recommendation

At this point I would keep:

Early Recovery
v2


because:

meaningful stress
realistic recovery
not too extreme
Late Stress
v3


because:

first version producing meaningful reproductive stress
Dual Stress
v2


because:

strong response
likely more realistic than v3

So the emerging "candidate experiment set" is:

Control

Early Recovery v2

Late Stress v3

Dual Stress v2


Those are the four treatments I would use next when creating the final comparison figures and determining whether GeoAquaCrop provides a convincing mechanistic explanation for the recovery behavior observed in your manuscript.
