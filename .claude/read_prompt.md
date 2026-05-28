# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"


Edit frontend/app.py only. Surgical edit. Fix palm rerun loop.

Add to session state defaults block (near top, with other defaults):
  if "palm_left_confirmed" not in st.session_state:
      st.session_state.palm_left_confirmed = False
  if "palm_right_confirmed" not in st.session_state:
      st.session_state.palm_right_confirmed = False
  if "_palm_left_image_name" not in st.session_state:
      st.session_state["_palm_left_image_name"] = None
  if "_palm_right_image_name" not in st.session_state:
      st.session_state["_palm_right_image_name"] = None

In the left palm upload block:
  - Ensure the entire validate + describe + success block is guarded by:
      if st.session_state["_palm_left_image_name"] != uploaded_left_palm.name:
  - At the end of a successful describe: set 
      st.session_state["_palm_left_image_name"] = uploaded_left_palm.name
      st.session_state.palm_left_confirmed = True
  - On uploader cleared (elif branch): also reset 
      st.session_state.palm_left_confirmed = False
      st.session_state.palm_left_str = None
      st.session_state["_palm_left_image_name"] = None

Apply the identical pattern to the right palm upload block 
using palm_right_confirmed, _palm_right_image_name, palm_right_str.

Remove any local bool variables used for confirmation state 
(e.g. confirmed = True / confirmed = False) — these do not 
survive reruns and are the source of the loop.

No other changes.