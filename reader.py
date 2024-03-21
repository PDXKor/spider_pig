import irsdk
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
import time
import logging
import dal

DB_RECREATE = False
DEV_LOG = False

if DEV_LOG:
    # Configure logging to write to a file, include the time, and set level to DEBUG
    logging.basicConfig(filename='reader.log', level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

def log(message):
    '''Log message for debugging if DEV_LOG is true.'''
    if DEV_LOG:
        logging.debug(message)

#this is our State class, with some helpful variables
class State:
    ir_connected = False
    last_car_setup_tick = -1
    init_time = None
    weekend_info = False
    init_datetime = None

def check_iracing():
    '''Checks for an active connection to iRacing. This should suppot multiple sessions being opened and closed.'''    
    
    if state.ir_connected and not (ir.is_initialized and ir.is_connected):
        # don't forget to reset your State variables
        state.ir_connected = False
        state.last_car_setup_tick = -1
        state.init_datetime = None
        state.weekend_info = False
        # we are shutting down ir library (clearing all internal variables)
        ir.shutdown()
        log('IRSDK Disconnected')
    
    elif not state.ir_connected and ir.startup() and ir.is_initialized and ir.is_connected:
        state.ir_connected = True
        # the init time is what we use to show that a new session has been initialized and we are using that time
        # as a unique identifier to track different sessions, this is because practice sessions run locally set
        # all the session id values to 0
        
        # Get the current UTC date and time
        current_utc_datetime = datetime.utcnow()
        
        # Format the date and time as a string
        formatted_utc_datetime = current_utc_datetime.strftime("%Y-%m-%d %H:%M:%S")
        state.init_datetime = formatted_utc_datetime

def log_telemetry(loop_counter):
    # time each loop to make sure we can hit <1/60th a second
    start_time = time.perf_counter()
    
    # you need this to freeze buffer for telemetry0

    ir.freeze_var_buffer_latest()
    t = ir['SessionTime'] 
    
    # some data we only store every 10 loops, this keeps the program running quickly
    if loop_counter == 0 or loop_counter % 10 == 0:
        # what we can do here is check for a change in the weekend info, but just store it once
        # we create a key that connects this telemetry this weekend info with any other info logged during the session 
        weekend_info = ir['WeekendInfo']
        log(weekend_info)
        
        # if we haven't logged the weekend info then log it, should only need to log it once
        if not state.weekend_info:
            weekend_info.pop('WeekendOptions')
            weekend_info.pop('TelemetryOptions')
            weekend = dal.WeekendInfo(state.init_datetime, **weekend_info)
            log(weekend) 
            weekend.insert()   
            state.weekend_info = weekend_info
        
        # grab the session info, get new each loop.
        session_info = ir['SessionInfo']
        log(session_info)
        
        # per session get session object and results position
        for s in session_info['Sessions']:
            session = dal.Session(InitDateTime = state.init_datetime,
                            SessionNum=s['SessionNum'],
                            SessionLaps=s['SessionLaps'],
                            SessionTime=s['SessionTime'],
                            SessionNumLapsToAvg=s['SessionNumLapsToAvg'],
                            SessionType=s['SessionType'],
                            SessionTrackRubberState=s['SessionTrackRubberState'],
                            SessionName=s['SessionName'],
                            SessionSubType=s['SessionSubType'],
                            SessionSkipped=s['SessionSkipped'],
                            SessionRunGroupsUsed=s['SessionRunGroupsUsed'],
                            SessionEnforceTireCompoundChange=s['SessionEnforceTireCompoundChange'])
            log(session)
            # session we just want to overwrite what we have
            # we delete the current session for the current init_datetime
            # then insert new
            session.delete(state.init_datetime)
            session.insert()
            
            dal.ResultPosition.delete(state.init_datetime)
            
            if 'ResultsPosition' in s:
                for r in s['ResultsPositions']:
                    result_position = dal.ResultPosition(state.init_datetime,**r)
                    log(result_position)
                    result_position.insert()

        # get info on drivers
        dal.Driver.delete(state.init_datetime)
        for d in ir['DriverInfo']['Drivers']:
            driver_data = dal.Driver.set_data(d)
            driver = dal.Driver(state.init_datetime,**driver_data)
            driver.insert()
            log(driver)
        
        # get SessionWeather
        # TODO add
        
        # get LapTiming
        lap_timing = dal.LapTiming.set_data(d)
        dal.LapTiming(state.init_datetime, **lap_timing).insert()
        
        '''
        lap_timing = dal.LapTiming(
            InitDateTime = state.init_datetime,
            Lap=ir["Lap"],
            LapBestLap=ir["LapBestLap"],
            LapBestLapTime=ir["LapBestLapTime"],
            LapBestNLapLap=ir["LapBestNLapLap"],
            LapBestNLapTime=ir["LapBestNLapTime"],
            LapCompleted=ir["LapCompleted"],
            LapCurrentLapTime=ir["LapCurrentLapTime"],
            LapDeltaToBestLap=ir["LapDeltaToBestLap"],
            LapDeltaToBestLap_DD=ir["LapDeltaToBestLap_DD"],
            LapDeltaToBestLap_OK=ir["LapDeltaToBestLap_OK"],
            LapDeltaToOptimalLap=ir["LapDeltaToOptimalLap"],
            LapDeltaToOptimalLap_DD=ir["LapDeltaToOptimalLap_DD"],
            LapDeltaToOptimalLap_OK=ir["LapDeltaToOptimalLap_OK"],
            LapDeltaToSessionBestLap=ir["LapDeltaToSessionBestLap"],
            LapDeltaToSessionBestLap_DD=ir["LapDeltaToSessionBestLap_DD"],
            LapDeltaToSessionBestLap_OK=ir["LapDeltaToSessionBestLap_OK"],
            LapDeltaToSessionLastlLap=ir["LapDeltaToSessionLastlLap"],
            LapDeltaToSessionLastlLap_DD=ir["LapDeltaToSessionLastlLap_DD"],
            LapDeltaToSessionLastlLap_OK=ir["LapDeltaToSessionLastlLap_OK"],
            LapDeltaToSessionOptimalLap=ir["LapDeltaToSessionOptimalLap"],
            LapDeltaToSessionOptimalLap_DD=ir["LapDeltaToSessionOptimalLap_DD"],
            LapDeltaToSessionOptimalLap_OK=ir["LapDeltaToSessionOptimalLap_OK"],
            LapDist=ir["LapDist"],
            LapDistPct=ir["LapDistPct"],
            LapLasNLapSeq=ir["LapLasNLapSeq"],
            LapLastLapTime=ir["LapLastLapTime"],
            LapLastNLapTime=ir["LapLastNLapTime"]
        )
        lap_timing.insert()
        '''
        
        # get TireData
        # Manually creating an instance of Tires
        tires = dal.Tires(
            InitDateTime = state.init_datetime,
            LFtempCL=ir["LFtempCL"],
            LFtempCM=ir["LFtempCM"],
            LFtempCR=ir["LFtempCR"],
            LRtempCL=ir["LRtempCL"],
            LRtempCM=ir["LRtempCM"],
            LRtempCR=ir["LRtempCR"],
            RFtempCL=ir["RFtempCL"],
            RFtempCM=ir["RFtempCM"],
            RFtempCR=ir["RFtempCR"],
            RRtempCL=ir["RRtempCL"],
            RRtempCM=ir["RRtempCM"],
            RRtempCR=ir["RRtempCR"],
            LFwearL=ir["LFwearL"],
            LFwearM=ir["LFwearM"],
            LFwearR=ir["LFwearR"],
            LRwearL=ir["LRwearL"],
            LRwearM=ir["LRwearM"],
            LRwearR=ir["LRwearR"],
            RFwearL=ir["RFwearL"],
            RFwearM=ir["RFwearM"],
            RFwearR=ir["RFwearR"],
            RRwearL=ir["RRwearL"],
            RRwearM=ir["RRwearM"],
            RRwearR=ir["RRwearR"],
            TireLF_RumblePitch=ir["TireLF_RumblePitch"],
            TireLR_RumblePitch=ir["TireLR_RumblePitch"],
            TireRF_RumblePitch=ir["TireRF_RumblePitch"],
            TireRR_RumblePitch=ir["TireRR_RumblePitch"],
            TireSetsAvailable=ir["TireSetsAvailable"],
            TireSetsUsed=ir["TireSetsUsed"],
            FrontTireSetsAvailable=ir["FrontTireSetsAvailable"],
            FrontTireSetsUsed=ir["FrontTireSetsUsed"],
            LeftTireSetsAvailable=ir["LeftTireSetsAvailable"],
            LeftTireSetsUsed=ir["LeftTireSetsUsed"],
            LFTiresAvailable=ir["LFTiresAvailable"],
            LFTiresUsed=ir["LFTiresUsed"],
            RFTiresAvailable=ir["RFTiresAvailable"],
            RFTiresUsed=ir["RFTiresUsed"],
            RRTiresAvailable=ir["RRTiresAvailable"],
            RRTiresUsed=ir["RRTiresUsed"]
        )

    # the main telem object for the player
    racing_telemetry_data = dal.RacingTelemetryData(
        InitDateTime=state.init_datetime,
        SessionTime=t,
        Lap=ir["Lap"],
        LapDist=ir["LapDist"],
        LapDistPct=ir["LapDistPct"],
        Brake=ir["Brake"],
        BrakeABSactive=ir["BrakeABSactive"],
        BrakeRaw=ir["BrakeRaw"],
        Clutch=ir["Clutch"],
        ClutchRaw=ir["ClutchRaw"],
        FuelLevel=ir["FuelLevel"],
        FuelLevelPct=ir["FuelLevelPct"],
        FuelPress=ir["FuelPress"],
        FuelUsePerHour=ir["FuelUsePerHour"],
        Gear=ir["Gear"],
        HandbrakeRaw=ir["HandbrakeRaw"],
        SteeringWheelAngle=ir["SteeringWheelAngle"],
        SteeringWheelAngleMax=ir["SteeringWheelAngleMax"],
        SteeringWheelLimiter=ir["SteeringWheelLimiter"],
        SteeringWheelMaxForceNm=ir["SteeringWheelMaxForceNm"],
        SteeringWheelPctDamper=ir["SteeringWheelPctDamper"],
        SteeringWheelPctIntensity=ir["SteeringWheelPctIntensity"],
        SteeringWheelPctSmoothing=ir["SteeringWheelPctSmoothing"],
        SteeringWheelPctTorque=ir["SteeringWheelPctTorque"],
        SteeringWheelPctTorqueSign=ir["SteeringWheelPctTorqueSign"],
        SteeringWheelPctTorqueSignStops=ir["SteeringWheelPctTorqueSignStops"],
        SteeringWheelPeakForceNm=ir["SteeringWheelPeakForceNm"],
        SteeringWheelTorque=ir["SteeringWheelTorque"],
        #SteeringWheelTorque_ST=ir["SteeringWheelTorque_ST"],
        Throttle=ir["Throttle"],
        ThrottleRaw=ir["ThrottleRaw"],
        TrackTempCrew=ir["TrackTempCrew"],
    )
    
    #lap_timing = dal.LapTiming.set_data(d)
    #dal.LapTiming(state.init_datetime, **lap_timing).insert()
    race_telem = dal.RacingTelemetryData.set_data(ir)
    dal.LapTiming(state.init_datetime, **race_telem)

    log(racing_telemetry_data)
    #racing_telemetry_data.insert()
    
    # check loop performance
    end_time = time.perf_counter()
    time_taken = end_time - start_time
    log(f'Main loop took: {time_taken}')

if __name__ == '__main__':    
    
    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    
    # rebuild db if necessary
    if DB_RECREATE:
        dal.setup_db()
    
    try:
        loop_counter = 0
        # infinite loop
        while True:
            current_time= time.strftime("%H:%M:%S")

            # check if we are connected to iracing
            print(f"\rChecking for active iRacing session, last checked {current_time}", end="")
            check_iracing()
            
            # if we are, then process data
            if state.ir_connected:
                log(f'iRacing session found, logging current session at {current_time}')
                log_telemetry(loop_counter)
            
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            loop_counter += 1
            time.sleep(.2)
    
    except KeyboardInterrupt:
        pass