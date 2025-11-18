Here is your Markdown file exactly as requested — you can copy/paste this straight into:
~/Work/PycharmProjects/PythonProject/notes/2025-11-18_Gooee_Progress.md


# Headphones / Voice Chat Setup (Turtle Beach)
Before continuing development, make sure the headset is working for voice mode:
- Plug in Turtle Beach headset
- Open **Settings → Sound**
- Set **Input = Turtle Beach Mic**
- Set **Output = Turtle Beach Headphones**
- In the browser (Brave or Chromium), click the 🔒 icon → allow microphone
- Reload ChatGPT and click the 🎤 mic icon

If the mic is detected but silent:
- Check pavucontrol (`sudo apt install pavucontrol`)
- Set the headset profile to **Analog Stereo Duplex**
- Ensure input level moves while talking
- If needed: `pactl list short sources` and `pactl set-default-source <id>`

---

# Gooee NodeView + System Architect Notes
*(latest state — consolidated)*

## 1. Project Architecture

HVAC/
gui/
app_state.py
tabs/
heat_loss_tab.py
widgets/
node_view.py
core/
data/
notes/

### UI Layers vs Model Layers
| UI Layer | Data Layer |
|----------|------------|
| NodeView / QGraphics | Room / PipeRun / System |
| Right-click menus    | U-value / Y-value / pipe model |
| Drag & drop          | Stored positions only |
| Connectors           | Real hydraulic links later |

The GUI **never stores engineering data** — it only displays & manipulates it.

---

## 2. Node Movement Rules (Important)
- Dragging = **visual only**
- Engineering data (U-values, pipe lengths, flow) **not recalculated until requested**
- Node stores reference like: `node.model = <Room>`
- When solver runs, it reads latest `.pos()` for distances
- Safe, scalable, no “live recalculation during dragging”

---

## 3. Current Feature Progress
### NodeView Completed
✔ QGraphicsView + Scene  
✔ Mouse wheel zoom  
✔ Middle mouse panning  
✔ Snap-to-grid  
✔ Moveable nodes  
✔ Basic example nodes  

### Next Features Planned
⬜ Right-click menu:
   - Delete
   - Duplicate
   - Rename/Edit text
   - Properties / formulas

⬜ Connectors (pipe links)
⬜ Model reference → nodes track associated `Room`, `Pipe`, etc.
⬜ Save/load layout (JSON)
⬜ Appearance themes

---

## 4. Pipe Calculation Integration Plan
Pipe solver will use:

length = distance(nodeA.position, nodeB.position)
Then apply:
✔ Darcy-Weisbach  
✔ Colebrook  
✔ K-factor + effective length  
✔ Heat loss using IHVE/BSRIA data

No recalculation until “Run Pipes” or similar is pressed.

---

## 5. Heat Loss Model Status (GUI Layer)
HeatLossTab basic version exists:
- A×U×ΔT
- IFHL / environmental ready
- Table of elements
- Auto-updates
- Checkbox-based calculation modes

Skill-based UI control is implemented via:

SkillLevel.BASIC
SkillLevel.INTERMEDIATE
SkillLevel.ADVANCED

---

## 6. Short-Term TODO
### GUI
[ ] Add right-click menu  
[ ] Connectors between nodes  
[ ] Node → Model linking  
[ ] Save/load JSON  

### Engineering
[ ] PipeRun class finalization  
[ ] IHVE formula + emissivity integration  
[ ] Basic system manager to hold Rooms & Pipes  

### Documentation / Notes
[ ] Start `docs/` or keep storing `.md` in `notes/`  
[ ] Option to auto-generate an index.md  

---

## 7. Quick Command Reminders
Run NodeView test:

python3 HVAC/gui/widgets/node_view.py

Format code with black:

black HVAC/gui/widgets/node_view.py

List duplicated `gui/` dirs (fixed earlier):

find . -maxdepth 2 -type d -name gui

---

## 8. Optional Future Items
- AutoCAD / DXF export
- Time-based dynamic heat model (Y-values)
- Pipe loss lookup tables (optional)
- Editable formula viewer
- Live diagram generation from model
- Embedded help / teaching mode

---

### Summary
You now have:
- A working visual node editor
- A growing heat loss UI
- Clean architectural separation
- A documented plan for next features
- A safe way to integrate pipe calculations
- A permanent record of where we are

**Next Restart Trigger Phrase:**
> Continue NodeView development
or
> Resume Gooee from this point

---

**End of File**


Just copy/paste that whole block into a .md file and you're set.
When you return, just say: “Continue from the nodeview file” and we’ll pick up instantly.
