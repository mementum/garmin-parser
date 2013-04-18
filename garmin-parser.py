#!/usr/bin/env python
# -*- coding: latin-1; py-indent-offset:4 -*-
################################################################################
#
# This file is part of Garmin Parser
#
# Garmin Parser is free software; you can redistribute it
# and/or modify it under the terms of the GNU General Public
# License as published by the Free Software Foundation; either
# version 2, or (at your option) any later version.
#
# Garmin Parser is distributed in the hope that it will be
# useful, but WITHOUT ANY WARRANTY; without even the implied
# warranty of MERCHANTABILITY or FITNESS FOR A PARTICULAR
# PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public
# License along with program; see the file COPYING. If not,
# write to the Free Software Foundation, Inc., 59 Temple Place
# - Suite 330, Boston, MA 02111-1307, USA.
#
# Copyright 2009
#
# FILE:
# garmin-parser.py
#
# DESCRIPTION:
#
# NOTES:
#
###############################################################################

#from datetime import datetime, time, timedelta
import datetime
import xml.etree.ElementTree

class CET_t(datetime.tzinfo):

    def __init__(self):         # DST starts last Sunday in March
        d = datetime.datetime(datetime.datetime.utcnow().year, 4, 1)   # ends last Sunday in October
        self.dston = d - datetime.timedelta(days=d.weekday() + 1)
        d = datetime.datetime(datetime.datetime.utcnow().year, 11, 1)
        self.dstoff = d - datetime.timedelta(days=d.weekday() + 1)

    def utcoffset(self, dt):
        return datetime.timedelta(hours=1) + self.dst(dt)

    def dst(self, dt):
        if self.dston <=  dt.replace(tzinfo=None) < self.dstoff:
            return datetime.timedelta(hours=1)
        else:
            return datetime.timedelta(0)

    def tzname(self,dt):
        return "GMT +1"


def fixDateTime( p_timedate):
    return datetime.datetime(year = p_timedate.year,
                             month = p_timedate.month,
                             day = p_timedate.day,
                             hour = p_timedate.hour,
                             minute = p_timedate.minute,
                             second = p_timedate.second,
                             tzinfo=CET_t())

class NS_t:
    """
    Improved helper class for ElementTree Xpath Search with namespaces
    Found at: http://infix.se/2007/02/21/xpath-friendlier-elementtree-namespace-helper
    """
    def __init__(self, uri):
        self.uri = uri
    def __getattr__(self, tag):
        return self.uri + tag
    def __call__(self, path):
        return "/".join((tag not in ("", ".", "*"))
                        and getattr(self, tag)
                        or tag
                        for tag in path.split("/"))
    def __str__(self):
        return self.uri

class Position_t(object):
    s_spacing = "        "
    def __init__(self, p_element = None):
        if p_element != None:
            self.m_latitude = float( p_element.find(g_NS("./LatitudeDegrees")).text)
            self.m_longitude = float( p_element.find(g_NS("./LongitudeDegrees")).text)
        else:
            self.m_latitude = 0.0
            self.m_longitude = 0.0

    def __str__(self):

        l_str = self.s_spacing + "-- Position Begin --\n"

        l_str += self.s_spacing + "  Latitude: " + str(self.m_latitude) + "\n"
        l_str += self.s_spacing + "  Longitude: " + str(self.m_longitude) + "\n"

        l_str += self.s_spacing + "-- Position End --\n"

        return l_str
    
class Trackpoint_t(object):
    s_spacing = "      "
    def __init__(self, p_element, p_prevTrackpoint = None):

        l_time = datetime.datetime.strptime(p_element.find(g_NS("./Time")).text, "%Y-%m-%dT%H:%M:%SZ")
        self.m_time = fixDateTime(l_time)

        l_elPosition = p_element.find(g_NS("./Position"))
        if l_elPosition != None:
            self.m_position = Position_t(l_elPosition)
        else:
            if p_prevTrackpoint != None:
                self.m_position = p_prevTrackpoint.m_position
            else:
                self.m_position = Position_t()

        try:
            self.m_altitude = float(p_element.find(g_NS("./AltitudeMeters")).text)
        except:
            if p_prevTrackpoint != None:
                self.m_altitude = p_prevTrackpoint.m_altitude
            else:
                self.m_altitude = 0.0

        try:
            self.m_distance = float(p_element.find(g_NS("./DistanceMeters")).text)
        except:
            if p_prevTrackpoint != None:
                self.m_distance = p_prevTrackpoint.m_distance
            else:
                self.m_distance = 0.0

        try:
            self.m_heartrate = int(p_element.find(g_NS("./HeartRateBpm/Value")).text)
        except:
            if p_prevTrackpoint != None:
                self.m_heartrate = p_prevTrackpoint.m_heartrate
            else:
                self.m_heartrate = 0

        try:
            self.m_sensorstate = p_element.find(g_NS("./SensorState")).text
        except:
            if p_prevTrackpoint != None:
                self.m_sensorstate = p_prevTrackpoint.m_sensorstate
            else:
                self.m_sensorstate = "Absent"

    def __str__(self):

        l_str = self.s_spacing + "-- Trackpoint Begin --\n"

        l_str += self.s_spacing + "  Time: " + self.m_time.__str__() + "\n"
        l_str += self.m_position.__str__()
        l_str += self.s_spacing + "  Altitude (meters): " + str(self.m_altitude) + "\n"
        l_str += self.s_spacing + "  Distance (meters): " + str(self.m_distance) + "\n"
        l_str += self.s_spacing + "  Heartrate (bpm): " + str(self.m_heartrate) + "\n"
        l_str += self.s_spacing + "  Sensor State: " + self.m_sensorstate + "\n"

        l_str += self.s_spacing + "-- Trackpoint End --\n"

        return l_str


class Lap_t(object):
    s_spacing = "    "
    def __init__(self, p_element):
        l_starttime = datetime.datetime.strptime(p_element.get("StartTime"), "%Y-%m-%dT%H:%M:%SZ")
        self.m_starttime = fixDateTime(l_starttime)

        self.m_totaltime = datetime.timedelta( seconds = int(float(p_element.find(g_NS("./TotalTimeSeconds")).text)))
        self.m_distance = float(p_element.find(g_NS("./DistanceMeters")).text)
        self.m_maxspeed = float(p_element.find(g_NS("./MaximumSpeed")).text)
        self.m_calories = int(p_element.find(g_NS("./Calories")).text)

        try:
            self.m_avgHeartrate = int(p_element.find(g_NS("./AverageHeartRateBpm/Value")).text)
        except:
            self.m_avgHeartrate = 0

        try:
            self.m_maxHeartrate = int(p_element.find(g_NS("./MaximumHeartRateBpm/Value")).text)
        except:
            self.m_maxHeartrate = 0

        self.m_intensity = p_element.find(g_NS("./Intensity")).text
        self.m_trigger = p_element.find(g_NS("./TriggerMethod")).text

        self.m_trackpoints = []

        l_prevTrackpoint = None
        for l_trackpoint in p_element.findall(g_NS("./Track/Trackpoint")):

            l_newTrackpoint = Trackpoint_t(l_trackpoint, l_prevTrackpoint)

            self.m_trackpoints.append(l_newTrackpoint)

            l_prevTrackpoint = l_newTrackpoint

    def __str__(self):

        l_str = self.s_spacing + "-- Begin Lap --\n"

        l_str += self.s_spacing + "  Start Time: " + self.m_starttime.__str__() + "\n"
        l_str += self.s_spacing + "  Total Time (seconds): " + self.m_totaltime.__str__() + "\n"
        l_str += self.s_spacing + "  Distance (meters): " + str(self.m_distance) + "\n"
        l_str += self.s_spacing + "  Maximum Speed (???): " + str(self.m_maxspeed) + "\n"
        l_str += self.s_spacing + "  Calories (kcal): " + str(self.m_calories) + "\n"
        l_str += self.s_spacing + "  Average Heartrate (bpm): " + str(self.m_avgHeartrate) + "\n"
        l_str += self.s_spacing + "  Maximum Heartrate (bpm): " + str(self.m_maxHeartrate) + "\n"
        l_str += self.s_spacing + "  Trigger Method: " + self.m_trigger + "\n"
        
        l_str += self.s_spacing + "  Trackpoints: " + str(len(self.m_trackpoints)) + "\n"
        l_trackpointnum = 1
        for l_trackpoint in self.m_trackpoints:
            l_str += self.s_spacing + "  Trackpoint Num: " + str(l_trackpointnum) + "\n"
            l_trackpointnum += 1

            l_str += l_trackpoint.__str__()

        l_str += self.s_spacing + "-- End Lap --\n"

        return l_str

    def mergeLap(self, p_lap):
        self.m_trackpoints.extend( p_lap.m_trackpoints)

        self.m_totaltime += p_lap.m_totaltime
        self.m_distance += p_lap.m_distance
        self.m_maxspeed = max( self.m_maxspeed, p_lap.m_maxspeed)
        self.m_calories += p_lap.m_calories
        ## FIXME: Better calculation for the Average Heartrate
        self.m_avgHeartrate = int((self.m_avgHeartrate + p_lap.m_avgHeartrate)/2)
        self.m_maxHeartrate = max(self.m_avgHeartrate, p_lap.m_avgHeartrate)
        # All laps must have the same trigger method
        #self.m_trigger


class Activity_t(object):
    s_spacing = "  "

    def __init__(self, p_element):

        self.m_sport = p_element.get("Sport")

        #self.m_id = datetime.datetime.strptime(p_element.find(g_NS("./Id")).text, "%Y-%m-%dT%H:%M:%SZ")
        #self.m_id.replace(tzinfo=CET_t)
        self.m_id = p_element.find(g_NS("./Id")).text

        self.m_laps = []
        for l_lap in p_element.findall(g_NS("./Lap")):
            self.m_laps.append(Lap_t(l_lap))

    def __str__(self):

        l_str = self.s_spacing + "-- Begin Activity --\n"

        #l_str += self.s_spacing + "  Id (UTC): " + self.m_id.__str__() + "\n"
        l_str += self.s_spacing + "  Id: " + self.m_id + "\n"

        l_str += self.s_spacing + "  Laps: " + str(len(self.m_laps)) + "\n"
        l_lapnum = 1
        for l_lap in self.m_laps:

            l_str += self.s_spacing + "  Lap Num: " + str(l_lapnum) + "\n"
            l_lapnum +=1

            l_str += l_lap.__str__()

        l_str += self.s_spacing + "-- End Activity --\n"

        return l_str

    def mergeLaps(self, p_delete = True):
        for l_lap in self.m_laps[1:]:
            self.m_laps[0].mergeLap(l_lap)

        if(p_delete == True):
            del self.m_laps[1:]

class TrainingCenterDatabase_t(object):
    s_spacing = ""

    def __init__(self, p_file):
        l_elTree = xml.etree.ElementTree.parse(p_file)
        l_element = l_elTree.getroot()
        if l_element.tag[0] == "{":
            global g_NS
            g_NS = NS_t(l_element.tag.split("}")[0] + "}")

        self.m_activities = []

        for l_activity in l_element.findall(g_NS("./Activities/Activity")):
            self.m_activities.append(Activity_t(l_activity))

    def __str__(self):
        l_str = self.s_spacing + "-- TrainingCenterDatabase Begin\n"

        l_str += self.s_spacing + "  Activities: " + str(len(self.m_activities)) + "\n"

        l_activitynum = 1
        for l_activity in self.m_activities:
            l_str += self.s_spacing + "  Activity Num: " + str(l_activitynum) + "\n"
            l_activitynum += 1

            l_str += l_activity.__str__()

        l_str += self.s_spacing + "-- TrainingCenterDatabase End\n"

        return l_str


class StatsPerDistance_t(object):

    def __init__(self, p_activity, p_wantedLapDistance, p_totalKnownDistance):

        ## 1. See if there is any lap
        if len(p_activity.m_laps) == 0:
            return

        ## 2. Make a copy of the lap trackpoints
        l_trackpoints = list()
        for l_lap in p_activity.m_laps:
            l_trackpoints += l_lap.m_trackpoints
        
        ## 3. Reference to first lap and last trackpoint
        l_startlap = p_activity.m_laps[0]
        l_lastpoint = l_trackpoints[len(l_trackpoints)-1]

        ## 4. Precalculate values for the operations
        l_gpsError = round(((l_lastpoint.m_distance/p_totalKnownDistance) - 1.0),2)

        # 5. Initialize control variables for the loop
        l_curpointnum = 0
        l_totalpoints = len(l_trackpoints)

        l_distBase = p_wantedLapDistance
        l_dist = l_distBase

        l_prevLapTotalTime = 0


        
        for l_trackpoint in p_trackpoints:

            # Correct the trackpoint distance with the calculated gpsError
            l_adjPointDist = l_trackpoint.m_distance - (l_trackpoint.m_distance * l_gpsError)

            l_curpointnum += 1

            if l_adjPointDist >= p_wantedDistance or l_curpointnum == l_totalpoints:
                # Time used
                l_realLapTime = l_trackpoint.m_time - l_prevLapTime
                # Time used in seconds
                l_realLapTimeSeconds = l_realLapTime.days*3600*24 + l_realLapTime.seconds

                # Actual distance travelled in last lap
                l_realLapDist = l_adjPointDist - l_prevLapDist

                # Calculate pace (min/km) - The base is 1km
                l_lapPace = datetime.timedelta(seconds = int((1000*l_realLapTimeSeconds)/l_realLapDist))

                # Calculate approx time on "g_dist mark"
                if l_curtrackpoint == l_numtrackpoints:
                    g_dist -= g_basedist
                    g_dist += l_dist
                    g_basedist = l_dist

                #g_dist = round(g_dist, 3)

                l_approxLapTime = datetime.timedelta(seconds = int(( p_lapDistance * l_realLapTimeSeconds)/l_realLapDist))

                l_accumLapTime = (l_prevLapTime + l_approxLapTime) - l_startTime

                # Adjust the overall time
                l_approxTotalTime = l_prevLapTime + l_approxLapTime


        pass

    def __str__(self):
        return ""


#g_trainingDatabase = TrainingCenterDatabase_t("Alber-marathon-munich.xml")
g_trainingDatabase = TrainingCenterDatabase_t("DRo-marathon-munich.xml")

g_trainingDatabase.m_activities[0].mergeLaps()
#print g_trainingDatabase

l_distlist = [1000.0, 2000.0, 5000.0, 10000.0]
for l_disttocalc in l_distlist: 

    g_basedist = l_disttocalc
    g_dist = g_basedist

    g_starttime = g_trainingDatabase.m_activities[0].m_laps[0].m_starttime
    g_prevtime = g_starttime
    g_prevdist = 0.0
    g_accumlaptime = datetime.timedelta(0)

    l_time = datetime.timedelta(0)
    l_seconds = 0
    l_dist = 0.0
    l_pace = datetime.timedelta(0)
    l_laptimeapprox = datetime.timedelta(0)
    l_timeapprox = g_prevtime


    l_lasttrackpoint = g_trainingDatabase.m_activities[0].m_laps[0].m_trackpoints.pop()
    g_trainingDatabase.m_activities[0].m_laps[0].m_trackpoints.append(l_lasttrackpoint)

    g_error = round(((l_lasttrackpoint.m_distance - 42195)/42195),2)
#print "error: " + str(g_error)

    print "Km,Time,Accum Lap Time,Lap Time,Pace"
    l_numtrackpoints = len(g_trainingDatabase.m_activities[0].m_laps[0].m_trackpoints)
    l_curtrackpoint = 0
    for l_trackpoint in g_trainingDatabase.m_activities[0].m_laps[0].m_trackpoints:

        l_trackpoint.m_distance -= (l_trackpoint.m_distance*g_error)

        l_curtrackpoint += 1
        if l_trackpoint.m_distance >= g_dist or l_curtrackpoint == l_numtrackpoints:
            # Found a key item
            # Time used
            l_time = l_trackpoint.m_time - g_prevtime
            # Time used in seconds
            l_seconds = l_time.days*3600*24 + l_time.seconds

            # Actual distance travelled in last lap
            l_dist = l_trackpoint.m_distance - g_prevdist

            # Calculate pace
            # l_dist (meters) in l_seconds, then 1000m in x 
            l_pace = datetime.timedelta(seconds = int((1000*l_seconds)/l_dist))

            # Calculate approx time on "g_dist mark"
            if l_curtrackpoint == l_numtrackpoints:
                g_dist -= g_basedist
                g_dist += l_dist
                g_basedist = l_dist

            #g_dist = round(g_dist, 3)

            l_laptimeapprox = datetime.timedelta(seconds = int(( g_basedist * l_seconds)/l_dist))

            g_accumlaptime = (g_prevtime + l_laptimeapprox) - g_starttime

            # Adjust the overall time
            l_timeapprox = g_prevtime + l_laptimeapprox

            #------  Km -------------------------  Time of day ---------------- + Accum Lap Time ----------------------  Lap Time ----------------   Lap Pace ----
            print str(g_dist/1000) + "," + l_timeapprox.time().__str__() + "," + g_accumlaptime.__str__() + "," + l_laptimeapprox.__str__() + "," + l_pace.__str__()

            g_dist += g_basedist

            g_prevdist = l_trackpoint.m_distance

            g_prevtime = l_trackpoint.m_time




