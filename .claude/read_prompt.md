# Read Prompt

#Paste your instructions here. Then tell Claude: "Read .claude/read_prompt.md and execute"

Create tests/test_palm_quality.py

Mark all tests with @pytest.mark.integration

Load real files:
- left bytes: data/test_images/palm_left_test.jpg
- right bytes: data/test_images/palm_right_test.jpg  
- kundali: read data/default_user/kundali_summary.txt 
  if exists, else use "Sun in Aries, Moon in Cancer, 
  Jupiter in 7th house, Ketu mahadasha until 2025."

PALM_TERMS = ["left hand", "right hand", "life line", 
              "fate line", "heart line", "palm"]

Question for all 4 tests:
"What do my palm lines reveal about my career and wealth?"

Write 4 tests calling ask() directly from agent.astrologer:

1. test_no_context_no_hallucination
   ask(question only)
   Assert: none of PALM_TERMS in response["answer"].lower()

2. test_kundali_only_no_hallucination  
   ask(question + kundali_context)
   Assert: none of PALM_TERMS in response["answer"].lower()

3. test_palm_only_terms_present
   ask(question + palm_left + palm_right)
   Assert: any of PALM_TERMS in response["answer"].lower()

4. test_kundali_and_palm_both_referenced
   ask(question + kundali_context + palm_left + palm_right)
   Assert: any of PALM_TERMS in response["answer"].lower()
   Assert: any of ["period","antardasha","mahadasha","venus","ketu"] 
           in response["answer"].lower()

Use pytest. Add 2s sleep between GPT calls to avoid rate limit.
Report full response["answer"] for each test in test output 
using print() so we can review quality manually.
No other files modified.