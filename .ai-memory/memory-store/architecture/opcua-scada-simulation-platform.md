---
store_path: architecture/opcua-scada-simulation-platform
title: "OPC UA Industrial Engine & SCADA Simulation Platform"
summary: "OPC UA Industrial Engine & SCADA Simulation Platform"
priority: high
tags: [opcua, scada, python, asyncua, fastapi, simulation]
schema_version: 1.3
last_updated: "2026-08-12T08:59:21-04:00"
---

Implemented an OPC UA Industrial Engine & SCADA simulation platform using Python asyncua and FastAPI.
Features:
- OPC UA Server: `opc.tcp://0.0.0.0:4840/freeopcua/server/` with namespace `http://opcua.simulation.engine`.
- Device hierarchy: `Objects/IndustrialEngine/` with Folders `Status`, `Sensors`, `Controls`, `Alarms`.
- Telemetry & Physics: RPM, Coolant Temperature, Oil Pressure, Vibration, Total Hours, Trip Counter.
- RPC Methods: `StartEngine`, `StopEngine`, `SetTargetSpeed`, `ResetFault`, `InjectFault`.
- Web SCADA Dashboard: Modern glassmorphism UI running on FastAPI (`http://localhost:8000`), with real-time SVG gauges, multi-pen canvas oscilloscope, OPC UA Node Inspector tree browser, and alarm log.
