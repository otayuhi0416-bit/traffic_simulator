import os
import sys
import json
import csv
from datetime import datetime

# SUMO_HOMEが設定されていない場合のデフォルトを設定
if "SUMO_HOME" not in os.environ:
    os.environ["SUMO_HOME"] = "C:\\Program Files (x86)\\Eclipse\\Sumo"

if "SUMO_HOME" in os.environ:
    sys.path.append(os.path.join(os.environ["SUMO_HOME"], "tools"))
import traci

def load_signal_control(target_date, target_hour):
    control_csv = "resources/typeC_akita_2026_04/秋田県警_制御_202604.csv"
    signals = {}
    
    target_time_str = f"{target_date} {target_hour:02d}:00"
    print(f"Loading signal control data for {target_time_str}...")
    
    if not os.path.exists(control_csv):
        print(f"Signal control CSV not found: {control_csv}")
        return signals
        
    with open(control_csv, mode='r', encoding='cp932') as f:
        reader = csv.DictReader(f)
        for row in reader:
            time_str = row['時刻'].strip()
            if time_str == target_time_str:
                intersection_num = row['交差点番号'].strip()
                try:
                    cycle = float(row['サイクル長'])
                    splits = []
                    for i in range(1, 7):
                        val = row.get(f'スプリット＃{i}')
                        if val and val.strip():
                            splits.append(float(val))
                    
                    signals[intersection_num] = {
                        'cycle': cycle,
                        'splits': splits
                    }
                except ValueError:
                    continue
    print(f"Loaded control parameters for {len(signals)} intersections.")
    return signals

def apply_signal_timing(match_table, control_data):
    for intersection_num, data in match_table.items():
        tls_id = data['sumo_junction_id']
        
        if tls_id not in traci.trafficlight.getIDList():
            found = False
            for tid in traci.trafficlight.getIDList():
                if tid.startswith(tls_id) or tls_id.startswith(tid):
                    tls_id = tid
                    found = True
                    break
            if not found:
                continue
                
        if intersection_num not in control_data:
            continue
            
        control = control_data[intersection_num]
        cycle_len = control['cycle']
        splits = control['splits']
        
        if not splits:
            continue
            
        try:
            logics = traci.trafficlight.getCompleteRedYellowGreenDefinition(tls_id)
            if not logics:
                continue
                
            logic = logics[0]
            phases = list(logic.phases)
            
            fixed_time = 0.0
            green_phase_indices = []
            
            for i, phase in enumerate(phases):
                state = phase.state.lower()
                if 'y' in state or 'g' not in state:
                    fixed_time += phase.duration
                else:
                    green_phase_indices.append(i)
                    
            available_green_time = cycle_len - fixed_time
            if available_green_time <= 0:
                available_green_time = max(10.0, cycle_len)
                cycle_len = fixed_time + available_green_time
                
            num_green_phases = len(green_phase_indices)
            num_splits = len(splits)
            
            if num_green_phases == 0:
                continue
                
            split_sum = sum(splits)
            
            for i, phase_idx in enumerate(green_phase_indices):
                split_idx = i % num_splits
                split_val = splits[split_idx]
                phase_duration = (split_val / split_sum) * available_green_time
                phases[phase_idx].duration = max(5.0, round(phase_duration, 1))
                
            logic.phases = tuple(phases)
            traci.trafficlight.setProgramLogic(tls_id, logic)
            print(f"Applied custom timing to TLS {tls_id}: Cycle={cycle_len}s, Splits={splits}")
        except Exception as e:
            print(f"Failed to apply signal timing at TLS {tls_id}: {e}")

def run_simulation(target_date="2026/04/08", start_hour=8, use_gui=True):
    sumo_binary = "sumo-gui" if use_gui else "sumo"
    
    sumo_home = os.environ.get("SUMO_HOME")
    binary_path = os.path.join(sumo_home, "bin", sumo_binary)
    if not (os.path.exists(binary_path) or os.path.exists(binary_path + ".exe")):
        binary_path = sumo_binary
        
    config_file = "sim/akita.sumocfg"
    match_table_path = "data/match_table.json"
    
    if not os.path.exists(config_file):
        print(f"Error: SUMO config {config_file} not found.")
        sys.exit(1)
        
    with open(match_table_path, 'r', encoding='utf-8') as f:
        match_table = json.load(f)
        
    control_data = load_signal_control(target_date, start_hour)
    
    sumo_cmd = [binary_path, "-c", config_file, "--ignore-route-errors", "true"]
    
    print(f"Starting SUMO: {' '.join(sumo_cmd)}")
    traci.start(sumo_cmd)
    
    apply_signal_timing(match_table, control_data)
    
    print("Simulation started. Press Ctrl+C in terminal or close SUMO-GUI to end.")
    step = 0
    try:
        while step < 3600:
            traci.simulationStep()
            step += 1
            if step % 600 == 0:
                active_vehicles = traci.vehicle.getIDCount()
                print(f"Step {step}s (10-min mark). Active vehicles in network: {active_vehicles}")
    except traci.exceptions.FatalTraCIError:
        print("SUMO was closed by the user or terminated.")
    finally:
        try:
            traci.close()
        except Exception:
            pass
        print("Simulation finished.")

if __name__ == "__main__":
    target_date = "2026/04/08"
    start_hour = 8
    use_gui = True
    
    # 引数処理
    args = sys.argv[1:]
    if "--nogui" in args:
        use_gui = False
        args.remove("--nogui")
        
    if len(args) > 0:
        target_date = args[0]
    if len(args) > 1:
        start_hour = int(args[1])
        
    run_simulation(target_date, start_hour, use_gui=use_gui)
