#!/usr/bin/env python3

import asyncio
from mavsdk import System

async def run():

    drone = System()
    await drone.connect(system_address="udp://:14540")

    print("Waiting for drone to connect...")
    async for state in drone.core.connection_state():
        if state.is_connected:
            print(f"Drone discovered!")
            break

    print("Waiting for drone to have a global position estimate...")
    async for health in drone.telemetry.health():
        if health.is_global_position_ok:
            print("Global position estimate ok")
            break

    print("-- Arming")
    await drone.action.arm()

    # Setting takeoff altitude to 1.5m
    await drone.action.set_takeoff_altitude(1.5)
    print (await drone.action.get_takeoff_altitude())

    print("-- Taking off")
    await drone.action.takeoff()

    # maintaining 1.5m altitude for 30s
    print("-- Waiting for 30s")
    await asyncio.sleep(30)

    # lateral movement of 1m north and then back 1m 
    # await drone.action.goto_location()
    # print("-- Moved 1m North")
    # await drone.action.goto_location()
    # print("-- Moved back to original position")

    print("-- Landing")
    await drone.action.land()

if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(run())
