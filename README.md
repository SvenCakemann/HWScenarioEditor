# HWScenarioEditor
A small tool to edit the characters (and some other things) in the scenarios for Hyrule Warriors on Wii U.

This is used by decompressing the scenario files (on Wii U) with Auracomp: https://github.com/Venomalia/AuroraLib.Compression
Drag and drop a scenario file onto Auracomp. Then, you can open the resulting file with the Scenario Editor.

Drag and drop the edited scenario file onto the "compress.bat" file and it will create a new file that can be used on Cemu or on console.

----------
As of right now, this just changes out the captains present on the map. Potential values/unit placement shown in the tool has been a bit inconsistent (ie an ally might be listed under enemy, vice versa). Unit names with [Switch] in the title probably don't exist on Wii U and will cause a crash. 
