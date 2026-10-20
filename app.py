import streamlit as st
import pandas as pd
from collections import defaultdict, deque

st.set_page_config(
    page_title="Adaptive Mission Planning Simulator",
    page_icon="🧭",
    layout="wide",
)

st.title("🧭 Adaptive Mission Planning Simulator")
st.caption("Educational prototype • Fictional logistics scenario • Not for operational military use")

st.markdown(
    """
This prototype creates a small task plan, simulates a disruption, identifies downstream
dependencies, and generates a revised plan while keeping unaffected tasks unchanged where possible.
"""
)

# Fictional example data for a classroom simulation.
BASE_TASKS = [
    {"id": "T1", "task": "Load supplies", "location": "Base", "vehicle": "Vehicle A", "duration": 1, "depends_on": "None", "status": "Planned"},
    {"id": "T2", "task": "Deliver medical kits", "location": "North Hub", "vehicle": "Vehicle A", "duration": 2, "depends_on": "T1", "status": "Planned"},
    {"id": "T3", "task": "Deliver food supplies", "location": "East Hub", "vehicle": "Vehicle B", "duration": 2, "depends_on": "T1", "status": "Planned"},
    {"id": "T4", "task": "Collect equipment", "location": "East Hub", "vehicle": "Vehicle B", "duration": 1, "depends_on": "T3", "status": "Planned"},
    {"id": "T5", "task": "Return to base", "location": "Base", "vehicle": "Vehicle A", "duration": 1, "depends_on": "T2", "status": "Planned"},
]

def parse_dependencies(tasks):
    deps = {}
    for task in tasks:
        value = task["depends_on"]
        deps[task["id"]] = [] if value == "None" else [x.strip() for x in value.split(",") if x.strip()]
    return deps

def descendants(start_id, deps):
    children = defaultdict(list)
    for task_id, parents in deps.items():
        for parent in parents:
            children[parent].append(task_id)
    seen = set()
    queue = deque(children[start_id])
    while queue:
        item = queue.popleft()
        if item in seen:
            continue
        seen.add(item)
        queue.extend(children[item])
    return seen

def make_plan(tasks, disruption, delay_hours, unavailable_vehicle):
    revised = [dict(task) for task in tasks]
    deps = parse_dependencies(revised)
    affected = set()

    if disruption == "Vehicle unavailable":
        affected = {t["id"] for t in revised if t["vehicle"] == unavailable_vehicle}
        for task_id in list(affected):
            affected |= descendants(task_id, deps)
    elif disruption == "Task delayed":
        delayed_id = "T2"
        affected = {delayed_id} | descendants(delayed_id, deps)

    # Preserve tasks not in the affected set. Reassign tasks on the unavailable vehicle
    # to the other fictional vehicle; this is a transparent classroom heuristic.
    for task in revised:
        if task["id"] in affected:
            if disruption == "Vehicle unavailable" and task["vehicle"] == unavailable_vehicle:
                task["vehicle"] = "Vehicle B" if unavailable_vehicle == "Vehicle A" else "Vehicle A"
            task["status"] = "Replanned"
        else:
            task["status"] = "Unchanged"

    # A simple illustrative schedule: push dependent tasks later when T2 is delayed.
    if disruption == "Task delayed":
        for task in revised:
            if task["id"] == "T2":
                task["duration"] = int(task["duration"]) + int(delay_hours)
                task["status"] = "Delayed + replanned"

    return revised, affected

with st.sidebar:
    st.header("Simulation controls")
    disruption = st.selectbox(
        "Choose a simulated change",
        ["Vehicle unavailable", "Task delayed"],
    )
    unavailable_vehicle = "Vehicle A"
    delay_hours = 1
    if disruption == "Vehicle unavailable":
        unavailable_vehicle = st.selectbox("Vehicle that becomes unavailable", ["Vehicle A", "Vehicle B"])
    else:
        delay_hours = st.slider("Extra delay for medical-kit delivery (time units)", 1, 4, 2)
    st.info("All locations, vehicles, and tasks are fictional.")

original_df = pd.DataFrame(BASE_TASKS)
revised_tasks, affected_ids = make_plan(BASE_TASKS, disruption, delay_hours, unavailable_vehicle)
revised_df = pd.DataFrame(revised_tasks)

c1, c2, c3 = st.columns(3)
c1.metric("Tasks in plan", len(BASE_TASKS))
c2.metric("Tasks affected", len(affected_ids))
c3.metric("Tasks preserved", len(BASE_TASKS) - len(affected_ids))

st.subheader("1. Original mission plan")
st.dataframe(original_df, use_container_width=True, hide_index=True)

st.subheader("2. Change impact analysis")
if affected_ids:
    st.warning("Potentially affected tasks: " + ", ".join(sorted(affected_ids)))
    st.write("The simulator follows task dependencies to identify downstream work that may need review.")
else:
    st.success("No dependent tasks were identified as affected.")
st.caption("This is a simple dependency-based demonstration, not a validated operational planner.")

st.subheader("3. Revised mission plan")
st.dataframe(revised_df, use_container_width=True, hide_index=True)

st.subheader("4. What changed?")
changes = []
original_by_id = {task["id"]: task for task in BASE_TASKS}
for task in revised_tasks:
    old = original_by_id[task["id"]]
    details = []
    if task["vehicle"] != old["vehicle"]:
        details.append(f"vehicle: {old['vehicle']} → {task['vehicle']}")
    if task["duration"] != old["duration"]:
        details.append(f"duration: {old['duration']} → {task['duration']}")
    if task["status"] != "Unchanged":
        details.append(f"status: {task['status']}")
    if details:
        changes.append({"Task ID": task["id"], "Task": task["task"], "Change": "; ".join(details)})

if changes:
    st.dataframe(pd.DataFrame(changes), use_container_width=True, hide_index=True)
else:
    st.write("No changes were needed for this scenario.")

st.subheader("5. Interpretation")
st.markdown(
    """
- **Unchanged** means the task was outside the detected impact set.
- **Replanned** means the task was marked for review or reassignment after the simulated disruption.
- The current reassignment rule is intentionally simple. A future version could compare alternative plans using constraints, cost functions, or optimization algorithms.
"""
)

csv = revised_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download revised plan as CSV",
    data=csv,
    file_name="revised_mission_plan.csv",
    mime="text/csv",
)

st.divider()
st.caption("Prototype status: working baseline. Next steps: add dependency editing, plan scoring, test cases, and deployment.")
