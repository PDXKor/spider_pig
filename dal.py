import sqlite3
from dataclasses import dataclass, asdict, fields, field
import numpy as np
import os
from typing import Optional, Dict, Any, List

DB_PATH = 'race.db'
    
class DCExtender:
    
    def get_fields(self):
        return [field.name for field in fields(self)]
    
    @classmethod
    def create_table_sql(self):
        # TODO add doc string
        # build create_table_sql
        field_strings = []
        for field in fields(self):
            field_type = field.type
            if field_type == int:
                sql_type = 'INTEGER'
            elif field_type == str:
                sql_type = 'TEXT'
            elif field_type == float:
                sql_type = 'REAL'
            elif field_type == bool:
                sql_type = 'TEXT'
            else:
                raise ValueError(f"Unsupported data type: {field_type}")
            field_strings.append(f"{field.name} {sql_type}")
        fields_sql = ', '.join(field_strings)
        sql = f"CREATE TABLE {self.__name__} ({fields_sql})"       
        return sql 
    
    @classmethod
    def create_table(self, connection):
        # TODO add doc string
        # get create table sql
        sql = self.create_table_sql()
        
        # create table
        cursor = connection.cursor()
        cursor.execute(sql)
        connection.commit()
        print('-'*5,f'CREATED TABLE {self.__name__}')
        return None

    @classmethod
    def insert_statement(self): 
        # TODO add doc string               
        # get the list of fields
        fields_list = self.get_fields(self)
        fields_str = ", ".join(fields_list)
        
        # get the list of values
        values = ["?" for f in fields_list]
        values = ','.join(values)
        
        # create and return an insert statement with list of fields and values
        insert_statement = f'INSERT INTO {self.__name__} ({fields_str}) VALUES ({values})'
        return insert_statement      
    
    @classmethod
    def get_session_data(self, sub_session_id):
        # TODO add doc string
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        sql = f'SELECT * FROM {self.__name__} where sub_session_id = '+str(sub_session_id)
        cursor.execute(sql)
        rows = cursor.fetchall()
        if len(rows) == 0:
            return None
        return rows
    
    @classmethod
    def get_max_session_data(self,dict=True):
        # TODO add doc string
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        sql = f'SELECT * FROM {self.__name__} where sub_session_id = (SELECT MAX(sub_session_id) from {self.__name__})'
        cursor.execute(sql)
        rows = cursor.fetchall()
        return_data = []
        if len(rows) == 0:
            return None
        for row in rows:
            rd = self(*row)
            if dict:
                return_data.append(asdict(rd))
            else:
                return_data.append(rd)
        return return_data
    
    @classmethod
    def delete(self, init_datetime):
        # TODO add doc string
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        sql = f'DELETE FROM {self.__name__} where InitDateTime = "{init_datetime}"'
        cursor.execute(sql)
        conn.commit()

    def insert(self):
        # TODO add doc string
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        insert_sql = self.insert_statement()
        cursor.executemany(insert_sql,[self.unpack()])
        conn.commit()
          
    def unpack(self):
        # TODO add doc string
        return tuple(getattr(self, field.name) for field in fields(self))
    
    @classmethod
    def fields(self):
        return [field.name for field in fields(self)]
    
    @classmethod
    def set_data(self, data):
        return_data = {}
        field_names = self.fields()
        for field in field_names:
            if field != 'InitDateTime':
                # py IRSDK does not have the magic method __contains__
                # this is a workaround
                try:
                    _ = data[key]
                except KeyError:
                        return False

                if field not in data:
                    return_data[field] = None
                else:
                    return_data[field] = data[field]
        return return_data
        
        
@dataclass
class WeekendInfo(DCExtender):
    InitDateTime: str
    TrackName: str
    TrackID: int
    TrackLength: str
    TrackLengthOfficial: str
    TrackDisplayName: str
    TrackDisplayShortName: str
    TrackConfigName: str
    TrackCity: str
    TrackCountry: str
    TrackAltitude: str
    TrackLatitude: str
    TrackLongitude: str
    TrackNorthOffset: str
    TrackNumTurns: int
    TrackPitSpeedLimit: str
    TrackType: str
    TrackDirection: str
    TrackWeatherType: str
    TrackSkies: str
    TrackSurfaceTemp: str
    TrackAirTemp: str
    TrackAirPressure: str
    TrackWindVel: str
    TrackWindDir: str
    TrackRelativeHumidity: str
    TrackFogLevel: str
    TrackPrecipitation: str
    TrackCleanup: int
    TrackDynamicTrack: int
    TrackVersion: str
    SeriesID: int
    SeasonID: int
    SessionID: int
    SubSessionID: int
    LeagueID: int
    Official: int
    RaceWeek: int
    EventType: str
    Category: str
    SimMode: str
    TeamRacing: int
    MinDrivers: int
    MaxDrivers: int
    DCRuleSet: str
    QualifierMustStartRace: int
    NumCarClasses: int
    NumCarTypes: int
    HeatRacing: int
    BuildType: str
    BuildTarget: str
    BuildVersion: str

@dataclass
class ResultPosition(DCExtender):
    InitDateTime: str
    SessionId: int
    SubSessionId: int
    SessionNum:int
    SessionType: str
    SessionSubType:str
    Position: int
    ClassPosition: int
    CarIdx: int
    Lap: int
    Time: float
    FastestLap: int
    FastestTime: float
    LastTime: float
    LapsLed: int
    LapsComplete: int
    JokerLapsComplete: int
    LapsDriven: float
    Incidents: int
    ReasonOutId: int
    ReasonOutStr: str

@dataclass
class Session(DCExtender):
    InitDateTime: str
    SessionId: int
    SubSessionId: int
    SessionNum: int
    SessionLaps: str
    SessionTime: str
    SessionNumLapsToAvg: int
    SessionType: str
    SessionTrackRubberState: str
    SessionName: str
    SessionSubType: str
    SessionSkipped: int
    SessionRunGroupsUsed: int
    SessionEnforceTireCompoundChange: int
    #ResultsPositions: List[ResultPosition]

@dataclass
class RaceData(DCExtender):
    Sessions: List[Session]

@dataclass
class Driver(DCExtender):
    InitDateTime: str
    CarIdx: int
    UserName: str
    AbbrevName: str
    Initials: str
    UserID: int
    TeamID: int
    TeamName: str
    CarNumber: str
    CarNumberRaw: int
    CarPath: str
    CarClassID: int
    CarID: int
    CarIsPaceCar: int
    CarIsAI: int
    CarIsElectric: int
    CarScreenName: str
    CarScreenNameShort: str
    CarClassShortName: str
    CarClassRelSpeed: int
    CarClassLicenseLevel: int
    CarClassMaxFuelPct: str
    CarClassWeightPenalty: str
    CarClassPowerAdjust: str
    CarClassDryTireSetLimit: str
    CarClassColor: int
    CarClassEstLapTime: float
    IRating: int
    LicLevel: int
    LicSubLevel: int
    LicString: str
    LicColor: int
    IsSpectator: int
    CarDesignStr: str
    HelmetDesignStr: str
    SuitDesignStr: str
    BodyType: int
    FaceType: int
    HelmetType: int
    CarNumberDesignStr: str
    CarSponsor_1: int
    CarSponsor_2: int
    ClubName: str
    ClubID: int
    DivisionName: str
    DivisionID: int
    CurDriverIncidentCount: int
    TeamIncidentCount: int

@dataclass
class SessionWeather(DCExtender):
    AirDensity: float
    AirPressure: float
    AirTemp: float
    FogLevel: float
    Precipitation: float
    RelativeHumidity: float
    Skies: int
    SolarAltitude: float
    SolarAzimuth: float
    WeatherType: str
    WeatherVersion: str
    WindDir: float
    WindVel: float

@dataclass
class LapTiming(DCExtender):
    InitDateTime: str
    Lap: int
    LapBestLap: int
    LapBestLapTime: float
    LapBestNLapLap: int
    LapBestNLapTime: float
    LapCompleted: int
    LapCurrentLapTime: float
    LapDeltaToBestLap: float
    LapDeltaToBestLap_DD: float
    LapDeltaToBestLap_OK: bool
    LapDeltaToOptimalLap: float
    LapDeltaToOptimalLap_DD: float
    LapDeltaToOptimalLap_OK: bool
    LapDeltaToSessionBestLap: float
    LapDeltaToSessionBestLap_DD: float
    LapDeltaToSessionBestLap_OK: bool
    LapDeltaToSessionLastlLap: float
    LapDeltaToSessionLastlLap_DD: float
    LapDeltaToSessionLastlLap_OK: bool
    LapDeltaToSessionOptimalLap: float
    LapDeltaToSessionOptimalLap_DD: float
    LapDeltaToSessionOptimalLap_OK: bool
    LapDist: float
    LapDistPct: float
    LapLasNLapSeq: int
    LapLastLapTime: float
    LapLastNLapTime: float

@dataclass
class Tires(DCExtender):
    InitDateTime: str
    # Temperature Data
    LFtempCL: float
    LFtempCM: float
    LFtempCR: float
    LRtempCL: float
    LRtempCM: float
    LRtempCR: float
    RFtempCL: float
    RFtempCM: float
    RFtempCR: float
    RRtempCL: float
    RRtempCM: float
    RRtempCR: float

    # Wear Data
    LFwearL: float
    LFwearM: float
    LFwearR: float
    LRwearL: float
    LRwearM: float
    LRwearR: float
    RFwearL: float
    RFwearM: float
    RFwearR: float
    RRwearL: float
    RRwearM: float
    RRwearR: float

    #Other
    TireLF_RumblePitch: float
    TireLR_RumblePitch: float
    TireRF_RumblePitch: float
    TireRR_RumblePitch: float
    TireSetsAvailable: int
    TireSetsUsed: int
    FrontTireSetsAvailable: int
    FrontTireSetsUsed: int
    LeftTireSetsAvailable: int
    LeftTireSetsUsed: int
    LFTiresAvailable: int
    LFTiresUsed: int
    RFTiresAvailable: int
    RFTiresUsed: int
    RRTiresAvailable: int
    RRTiresUsed: int

@dataclass    
class RacingTelemetryData(DCExtender):
    #lap
    InitDateTime: str
    SessionTime: float
    Lap: int
    LapDist: float
    LapDistPct: float
    
    # Brake Data
    Brake: float
    BrakeABSactive: bool
    BrakeRaw: float 

    # Gear and Handbrake
    Gear: int
    HandbrakeRaw: float   

    # Clutch Data
    Clutch: float
    ClutchRaw: float

    # Steering and Throttle Data
    SteeringWheelAngle: float
    SteeringWheelAngleMax: float
    SteeringWheelLimiter: float
    SteeringWheelMaxForceNm: float
    SteeringWheelPctDamper: float
    SteeringWheelPctIntensity: float
    SteeringWheelPctSmoothing: float
    SteeringWheelPctTorque: float
    SteeringWheelPctTorqueSign: float
    SteeringWheelPctTorqueSignStops: float
    SteeringWheelPeakForceNm: float
    SteeringWheelTorque: float
    #SteeringWheelTorque_ST: float
    Throttle: float
    ThrottleRaw: float

    # Fuel Data
    FuelLevel: float
    FuelLevelPct: float
    FuelPress: float
    FuelUsePerHour: float    

    #Track Temp
    TrackTempCrew: float
    '''
    # Driver Control Data
    DCDriversSoFar: int
    DCLapStatus: str
    dcPitSpeedLimiterToggle: str
    dcStarter: str

    # Display and Repair Options
    DisplayUnits: int
    dpFastRepair: str
    dpFuelAddKg: float
    dpFuelAutoFillActive: str
    dpFuelAutoFillEnabled: str
    dpFuelFill: str
    dpLFTireChange: str
    dpLFTireColdPress: float
    dpLRTireChange: str
    dpLRTireColdPress: float
    dpRFTireChange: str
    dpRFTireColdPress: float
    dpRRTireChange: str
    dpRRTireColdPress: float
    dpWindshieldTearoff: str    

    # Engine Data
    Engine0_RPM: float
    EngineWarnings: int
    EnterExitReset: int
    FastRepairAvailable: int
    FastRepairUsed: int   

    # Track and Garage Data
    IsGarageVisible: str
    IsInGarage: str
    IsOnTrack: str
    IsOnTrackCar: str            
    OnPitRoad: str

    # Acceleration Data
    LatAccel: float
    LatAccel_ST: float
    LongAccel: float
    LongAccel_ST: float

    # Shock and Pressure Data
    LFbrakeLinePress: float
    LFcoldPressure: float
    LFshockDefl: float
    LFshockDefl_ST: float
    LFshockVel: float
    LFshockVel_ST: float
    LRbrakeLinePress: float
    LRcoldPressure: float
    LRshockDefl: float
    LRshockDefl_ST: float
    LRshockVel: float
    LRshockVel_ST: float
    
    # Pit and Repair Data
    PitOptRepairLeft: float
    PitRepairLeft: float
    PitSvFlags: int
    PitSvFuel: float
    PitSvLFP: float
    PitSvLRP: float
    PitSvRFP: float
    PitSvRRP: float
    PitSvTireCompound: str

    VelocityX: float
    VelocityX_ST: float
    VelocityY: float
    VelocityY_ST: float
    VelocityZ: float
    VelocityZ_ST: float
    VertAccel: float
    VertAccel_ST: float
    VidCapActive: str
    VidCapEnabled: str
    Voltage: float
    WaterLevel: float
    WaterTemp: float
    WindDir: float
    WindVel: float
    Yaw: float
    YawNorth: float
    YawRate: float
    YawRate_ST: float
    '''
    
def setup_db(db_path=DB_PATH, new_db=True):
    # TODO add docstring
    if new_db:
        #TODO add logging
        print('---CREATING NEW TELEMETRY DATABASE---')
        if os.path.exists(db_path):            
            # remove db
            os.remove(db_path)                        
            #create new db and tables tables
            conn = sqlite3.connect(DB_PATH)
            Session.create_table(conn)
            WeekendInfo.create_table(conn)
            Driver.create_table(conn)
            ResultPosition.create_table(conn)
            RacingTelemetryData.create_table(conn)
            LapTiming.create_table(conn)

            
    conn = sqlite3.connect(DB_PATH)
    conn.close()

if __name__ == '__main__':
    print(DB_PATH)