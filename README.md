Channel Hop
===========

Generates options for a round-trip car journey via channel ferry.

This code provides a framework for evaluating and ranking different
combinations of travel options for a simple A-to-B cross-channel car
trip. Data collection is on the user, but this makes actually using
said data more efficient.

Usage
-----

Given an *origin* and a *destination* and two datasets (car routes,
ferry crossings), the code will evaluate different combinations and
present the results.

Assuming there is at least one route option in the dataset to UK ferry
ports of interest from 'MyHouse' (assumed to be in the UK) to
'MyDestination' (assumed to be in FR).

	>>> my_trip = Trip('MyOrigin', 'MyDest', ferrydata, cardata)

Where ferrydata and cardata are lists of `exdata.FerryData` and
`exdata.CarData` objects providing relevant route data (and
variations).

Why?
----

Every year, at least once, we/I am faced with the task of comparing
routes and timings for the myriad of viable channel ferry crossings
for at least one group car trip away to the continent.  The comparison
is performed in order to satisfy a range of financial constraints and
miscellaneous preferences. Every year this process is streamlined a
smidgen; this is the next stage in evolution beyond a laborious,
incomplete and error-prone spreadsheet-based approach.

It's surprising how many combinations of options there can be for a
simple A-to-B return trip. This year there are nearly 300 permutations
(and we wondered why it was always such a headache) which was swiftly
chopped to 30 distinctly-presented choices based on some simple
constraints, then down to three by refining constraints based on
discussion with the group. Easy.

Limitations
-----------

As to be expected with this type of motivation, the program has now
served its purpose (for now!) and is not exactly user friendly,
complete or even sensible in some regards. I'm also no graph theorist,
and the implementation shows this. It'll likely see extension and
iterative improvement in accordance with personal need.
