import irsdk
import time
from dataclasses import dataclass, field, asdict
from datetime import datetime
import time
import logging
import dal

DB_RECREATE = True
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

        # if these are 0 it is a private sesssion
        session_id = ir['WeekendInfo']['SessionID']
        sub_session_id = ir['WeekendInfo']['SubSessionID']
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
                            SessionId = session_id,
                            SubSessionId = sub_session_id,
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
            
            if 'ResultsPositions' in s:
                # sitting between sessions will cause this to be a None value
                if s['ResultsPositions']:
                    for r in s['ResultsPositions']:
                        result_position = dal.ResultPosition(state.init_datetime,
                                                            session_id,
                                                            sub_session_id,
                                                            s['SessionNum'],
                                                            s['SessionType'],
                                                            s['SessionSubType'], 
                                                            **r)
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
        #race_telem = dal.RacingTelemetryData.set_data(ir)
        #dal.RacingTelemetryData(state.init_datetime, **race_telem).insert()
        lap_timing = dal.LapTiming.set_data(ir)
        dal.LapTiming(state.init_datetime, **lap_timing).insert()        
        
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


    race_telem = dal.RacingTelemetryData.set_data(ir)
    dal.RacingTelemetryData(state.init_datetime, **race_telem).insert()

    # check loop performance
    end_time = time.perf_counter()
    time_taken = end_time - start_time
    log(f'Main loop took: {time_taken}')
    return time_taken

if __name__ == '__main__':    
    
    # initializing ir and state
    ir = irsdk.IRSDK()
    state = State()
    
    # rebuild db if necessary
    if DB_RECREATE:
        dal.setup_db()
    
    try:
        loop_counter = 0
        while True:
            current_time= time.strftime("%H:%M:%S")
            # check if we are connected to iracing
            check_iracing()            
            # if we are, then process data
            if state.ir_connected:
                loop_time = log_telemetry(loop_counter)
                print(f'\r Log loop ran in {loop_time}{" "*40}', end='')
            else:
                print(f"\r Checking session {current_time}", end="")
            # sleep for 1 second
            # maximum you can use is 1/60
            # cause iracing updates data with 60 fps
            loop_counter += 1
            time.sleep(.2)
    
    except KeyboardInterrupt:
        pass