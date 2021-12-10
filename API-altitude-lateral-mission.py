#!/usr/bin/env python3

import asyncio
from mavsdk import System
from mavsdk.mission import (MissionItem, MissionPlan)

async def run(drone):
    #drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print("Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break

    curr_lat = 0.0
    curr_long = 0.0
    print("Fetching info at home location....")
    async for terrain_info in drone.telemetry.home():
        curr_lat = terrain_info.latitude_deg
        curr_long = terrain_info.longitude_deg
        break

    print_mission_progress_task = asyncio.ensure_future(
        print_mission_progress(drone))

    running_tasks = [print_mission_progress_task]
    termination_task = asyncio.ensure_future(
        observe_is_in_air(drone, running_tasks))

    mission_items = []
    # Taking off to 1.5m altitude and then hovering in position for 5s
    mission_items.append(MissionItem(curr_lat,
                                     curr_long,
                                     1.5,
                                     1,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     5,
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    # Moving 2m (~2.22m) to the north (with altitude and 1s wait)
    mission_items.append(MissionItem(curr_lat+0.00002,
                                     curr_long,
                                     1.5,
                                     1,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     1,
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))
    # Returning to first position (with altitude and 1s wait) 
    mission_items.append(MissionItem(curr_lat,
                                     curr_long,
                                     1.5,
                                     1,
                                     True,
                                     float('nan'),
                                     float('nan'),
                                     MissionItem.CameraAction.NONE,
                                     1,
                                     float('nan'),
                                     float('nan'),
                                     float('nan')))

    mission_plan = MissionPlan(mission_items)

    await drone.mission.set_return_to_launch_after_mission(True)

    print("-- Uploading mission")
    await drone.mission.upload_mission(mission_plan)

    print("-- Arming")
    await drone.action.arm()

    print("-- Starting mission")
    await drone.mission.start_mission()

    await termination_task

async def print_mission_progress(drone):
    async for mission_progress in drone.mission.mission_progress():
        print(f"Mission progress: "
              f"{mission_progress.current}/"
              f"{mission_progress.total}")

# Monitors whether the drone is flying or not and returns after landing
async def observe_is_in_air(drone, running_tasks):
    was_in_air = False
    async for is_in_air in drone.telemetry.in_air():
        if is_in_air:
            was_in_air = is_in_air
        if was_in_air and not is_in_air:
            for task in running_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            await asyncio.get_event_loop().shutdown_asyncgens()
            return

if __name__ == "__main__":
    drone = System()
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run(drone))
