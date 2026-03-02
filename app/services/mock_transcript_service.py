"""
Mock Transcript Service
Simulates Google Meet Transcript API responses for local development and testing.
Replace with real Meet API calls once access is provisioned.
"""

import random
from typing import Optional

# ─────────────────────────────────────────────────────────
# Sample Transcripts  (5 realistic medical scenarios)
# ─────────────────────────────────────────────────────────

SCENARIO_CHEST_PAIN = """Dr. Patel: Good morning, Mr. Johnson. What brings you in today?
Patient: I've been having this chest pain for about three days now. It's kind of scary.
Dr. Patel: I understand that's concerning. Can you describe the pain for me? Is it sharp, dull, or more of a pressure?
Patient: It's more like a tightness, right in the center of my chest. Sometimes it spreads a little to my left shoulder.
Dr. Patel: Does it come and go, or is it constant?
Patient: It comes and goes. It gets worse when I climb stairs or do anything physical.
Dr. Patel: Any shortness of breath, sweating, or nausea along with the tightness?
Patient: Yes, I get a little short of breath when it happens. No nausea though.
Dr. Patel: Have you had any similar episodes before?
Patient: Not like this. I had some heartburn before but nothing with the shoulder thing.
Dr. Patel: Any history of heart disease in your family?
Patient: My father had a heart attack at 58. I'm 52 now and that's... that's why I'm here.
Dr. Patel: That's very important information, thank you for telling me. What medications are you currently on?
Patient: Just aspirin once in a while for headaches. No regular medications.
Dr. Patel: Do you smoke or drink?
Patient: I quit smoking about 5 years ago. I drink socially, maybe a glass of wine on weekends.
Dr. Patel: I'm going to do a physical exam now. Let me check your blood pressure and listen to your heart. [Pause for examination] Your blood pressure is 148 over 92, which is elevated. Heart sounds are normal, no murmur. Lung fields are clear.
Patient: Is it serious, doctor?
Dr. Patel: Given your symptoms, family history, and blood pressure, I want to take this seriously. The radiation to your shoulder combined with exertional component is something we need to rule out cardiac cause for urgently.
Dr. Patel: Here's what I'm going to do: I'm ordering an EKG today, a troponin blood test, and a complete lipid panel. I also want you to have a stress test scheduled this week. I'm going to start you on low-dose aspirin daily — 81 mg — and I'd like you to avoid strenuous activity until we have the results.
Patient: Should I go to the ER?
Dr. Patel: Your current vitals are stable and you're not in active distress, so we can manage this in an outpatient setting for now. But if the chest pain becomes severe, constant, or you develop sweating, arm pain, or difficulty breathing — go to the ER immediately. Do you understand?
Patient: Yes doctor, I understand. Thank you.
Dr. Patel: I'll have my nurse set up the EKG right now and we'll have those labs drawn before you leave. Follow up with me in 48 hours once we have results. Take care, Mr. Johnson."""

SCENARIO_DIABETES = """Dr. Nguyen: Hi Mrs. Patel, come on in. How have you been managing since our last visit?
Patient: Hello doctor. Honestly, my blood sugars have been all over the place. My home readings have been anywhere from 95 to 280.
Dr. Nguyen: That's quite a range. How often are you checking?
Patient: Twice a day — morning fasting and before dinner.
Dr. Nguyen: What does your diet look like recently? Any changes?
Patient: I've been trying to watch carbs but it's been hard this past month with family visiting. There were a lot of celebrations, a lot of sweets.
Dr. Nguyen: That's understandable. What's your current insulin regimen?
Patient: I'm on 22 units of Lantus at night and Humalog sliding scale with meals.
Dr. Nguyen: Have you been following the sliding scale correctly?
Patient: Most of the time, but I sometimes forget the dinner dose.
Dr. Nguyen: I see. Let me look at your labs — your HbA1c today came back at 8.9%, which is up from 7.8% three months ago. That tells me your average blood sugar over the past three months has been running too high.
Patient: I was afraid of that.
Dr. Nguyen: Your kidney function is still normal — creatinine 0.9, eGFR above 90 — which is good. Your lipids show LDL at 112, we should work on getting that below 100. Blood pressure today is 134 over 82.
Patient: Are there any complications? My feet have been tingling at night.
Dr. Nguyen: The tingling in your feet is something we need to take seriously — it could be early peripheral neuropathy. I'm going to do a monofilament test today. [Pause] You have reduced sensation in the left great toe and the plantar surface of both feet.
Patient: What does that mean?
Dr. Nguyen: It means the nerves in your feet are starting to be affected by high blood sugar. This is reversible if we get your sugars under better control now. Here's our plan: I'm going to increase your Lantus to 28 units at night. I also want to add Metformin 500 mg twice daily if your kidney function stays normal. On the lipid side, I'm starting you on Atorvastatin 20 mg at bedtime. Please see our dietitian this week — I'll put in a referral. And daily foot inspection — check your feet every single day.
Patient: Okay doctor, I'll do my best.
Dr. Nguyen: I know it's a lot but you're doing the right things by coming in regularly. I want to see you in 6 weeks with a repeat HbA1c, fasting glucose, and lipids. Call us if your sugars are consistently above 250 or you have any foot wounds.
Patient: Thank you doctor, I really appreciate it."""

SCENARIO_PEDIATRIC_FEVER = """Dr. Williams: Hi there. And who do we have here?
Parent: This is my son, Ethan. He's 6 years old. He's had a fever since yesterday evening and I'm really worried.
Dr. Williams: I understand. How high has the fever gotten?
Parent: It was 102.8 at home last night. This morning it went up to 103.5 after I gave him Tylenol.
Dr. Williams: And how is he acting? Is he drinking fluids?
Parent: He's a little lethargic, more tired than usual. He had some juice this morning but he's not eating much.
Dr. Williams: Any cough, runny nose, or sore throat?
Parent: He said his throat hurts yesterday. No cough but his nose was running a little.
Dr. Williams: Any rash anywhere on his body?
Parent: I checked and I didn't see anything.
Dr. Williams: Has he been around anyone who was sick recently?
Parent: Yes, two kids in his class were out last week with strep throat.
Dr. Williams: That's very helpful. Any ear pulling or ear pain?
Parent: He hasn't said anything about his ears.
Dr. Williams: Let me take a look at him. [Pause for examination] Temperature right now is 103.1 rectally. Heart rate is 108 — elevated but expected with fever. He's alert, looking at me, which is reassuring. Let me look in his throat... I can see significant redness and there is tonsillar exudate — white patches on his tonsils. His lymph nodes under his jaw are swollen. Ears look clear bilaterally. Lungs sound clear.
Parent: What is it, doctor?
Dr. Williams: I'm going to do a rapid strep test because what I'm seeing is very consistent with streptococcal pharyngitis — strep throat. [Pause] The test is positive. Ethan has strep throat.
Parent: Oh no. Will he be okay?
Dr. Williams: Absolutely — strep throat is very treatable with antibiotics. I'm prescribing Amoxicillin 250 milligrams twice daily for 10 days. It's very important he completes the full course even if he feels better in a couple of days.
Parent: He's not allergic to penicillin as far as we know.
Dr. Williams: Great. For comfort, continue Tylenol for fever — you can alternate with Motrin every 3 to 4 hours. Push fluids — popsicles, cold water, broth. He should stay home from school for at least 24 hours after starting antibiotics and until the fever is gone.
Parent: When should I be worried and call?
Dr. Williams: Call us if the fever goes above 104, if he develops a rash — especially a sandpaper-like rash — has difficulty breathing or swallowing, refuses all fluids, or becomes very difficult to arouse. Otherwise follow up if no improvement in 48 to 72 hours on antibiotics.
Parent: Thank you so much doctor.
Dr. Williams: He should start feeling better very quickly once the antibiotics kick in. Take care."""

SCENARIO_HYPERTENSION = """Dr. Singh: Good afternoon, Mr. Thompson. Let me pull up your chart. Your last visit was about three months ago. How have you been?
Patient: Pretty good overall. I've been trying to cut down on salt like you said.
Dr. Singh: That's great to hear. Are you still on the lisinopril 10 mg daily?
Patient: Yes. But I sometimes forget on weekends.
Dr. Singh: The consistency is very important for blood pressure control. What's your home blood pressure reading been like?
Patient: Usually around 140 to 145 over 85 to 90 in the mornings.
Dr. Singh: I see. Your reading today is 146 over 88 — still above our target of under 130 over 80. Let me review your last labs: BMP from two weeks ago shows potassium 4.1, creatinine 1.0, eGFR 78. All within normal range. Lipid panel shows LDL 141, which we need to work on.
Patient: I've been trying to exercise. I go for a 20-minute walk three times a week.
Dr. Singh: That's a great start. Can you try to get that up to five days a week? Even a brisk 30-minute walk daily makes a big difference for blood pressure.
Patient: I can try. I also wanted to ask, my ankles have been a little swollen at the end of the day. Is that related?
Dr. Singh: It could be. Let me check. [Pause] There's mild bilateral pitting edema in the ankles — about 1 plus. This can sometimes be a side effect of calcium channel blockers, though you're not on one. With lisinopril it's less common. Are you sitting for long periods at work?
Patient: Yes, I'm at a desk most of the day.
Dr. Singh: That's likely contributing. Elevating your legs when you're seated and short walks every hour will help. Given your blood pressure is still not at target despite lisinopril and lifestyle changes, I'd like to add a second medication — amlodipine 5 mg once daily. This should help bring those numbers down. The ankle swelling is something to monitor since amlodipine can occasionally worsen pedal edema.
Patient: Any side effects I should know about?
Dr. Singh: The main ones are flushing and ankle swelling. If swelling worsens significantly, let me know and we'll reassess. I'm also going to start you on Atorvastatin 20 mg for your LDL.
Patient: Another medication?
Dr. Singh: I know it feels like a lot. But high cholesterol along with blood pressure significantly multiplies your cardiac risk. Let's give it three months and check your labs again.
Patient: Alright, doctor. I'll give it a try.
Dr. Singh: Perfect. Follow up in 3 months. If your home readings are still elevated after 2 weeks on the new medication, call us. Bring a 2-week log of your home BP readings to the next visit."""

SCENARIO_ANXIETY = """Dr. Ramirez: Hello Sarah, it's good to see you. How are you doing since our last session?
Patient: Honestly, not great. The anxiety has been really bad the past two weeks.
Dr. Ramirez: I'm sorry to hear that. Can you tell me more about what's been happening?
Patient: I've been waking up at 2 or 3 AM and I can't go back to sleep. My heart races for no reason. I feel on edge all the time.
Dr. Ramirez: On a scale of zero to ten, how would you rate your anxiety overall this week?
Patient: Probably a 7 or 8, most days.
Dr. Ramirez: That's significant. Are you still doing the breathing exercises we talked about?
Patient: I try, but when the anxiety hits it's hard to remember to do them.
Dr. Ramirez: That's very common. When you're in the middle of an anxiety response, your cognitive access is limited. Have there been any specific triggers lately?
Patient: Work has been really stressful. I have a big project deadline and my manager has been very critical lately. I feel like I'm failing.
Dr. Ramirez: Are you having any thoughts of harming yourself or others?
Patient: No, nothing like that. I just feel overwhelmed and exhausted.
Dr. Ramirez: I hear you. Has there been any depression — low mood, loss of interest in things you enjoy?
Patient: A little, yeah. I haven't been going to my yoga classes that I usually love.
Dr. Ramirez: That's a meaningful change. Are you still taking the Sertraline 50 mg we started three months ago?
Patient: Yes, every morning.
Dr. Ramirez: How has your appetite and energy been?
Patient: Appetite is okay. Energy is low, especially in the afternoons.
Dr. Ramirez: Based on what you're describing — the elevated anxiety scores, the sleep disruption, low energy, and withdrawal from activities — I think we should increase your Sertraline to 100 mg. The 50 mg dose may not be giving you enough coverage.
Patient: Will that make me feel worse at first?
Dr. Ramirez: For some people there's a brief adjustment period of increased anxiety in the first one to two weeks when titrating up — this is normal and temporary. If it feels like too much, call us right away.
Patient: Okay. Is there anything else I can do?
Dr. Ramirez: Yes. I want you to try sleep hygiene — no screens 30 minutes before bed, consistent sleep and wake times even on weekends. Also, making a small behavioral commitment: can you attend one yoga class this week?
Patient: I think I can do one.
Dr. Ramirez: That's great — behavioral activation is very powerful for both anxiety and mood. I also want to refer you to our psychologist for six sessions of CBT — cognitive behavioral therapy — which has very strong evidence for generalized anxiety.
Patient: I've heard of that. I'm open to it.
Dr. Ramirez: Wonderful. I'll put in that referral today. Check back in with me in four weeks. If the anxiety or sleep gets significantly worse before then, please call us or go to urgent care.
Patient: Thank you doctor, I really appreciate your time."""

# ─────────────────────────────────────────────────────────
# Service
# ─────────────────────────────────────────────────────────

SCENARIOS: dict[str, str] = {
    "chest_pain": SCENARIO_CHEST_PAIN,
    "diabetes": SCENARIO_DIABETES,
    "pediatric_fever": SCENARIO_PEDIATRIC_FEVER,
    "hypertension": SCENARIO_HYPERTENSION,
    "anxiety": SCENARIO_ANXIETY,
}


class MockTranscriptService:
    """
    Simulates the Google Meet Transcript API.
    Returns pre-written realistic doctor-patient consultation transcripts.

    Usage:
        service = MockTranscriptService()
        transcript = service.get_mock_transcript()          # random scenario
        transcript = service.get_mock_transcript("diabetes") # specific scenario
    """

    def get_mock_transcript(self, scenario: Optional[str] = None) -> str:
        """
        Returns a formatted doctor-patient transcript string.

        Args:
            scenario: One of 'chest_pain', 'diabetes', 'pediatric_fever',
                      'hypertension', 'anxiety'. If None, picks a random one.

        Returns:
            A multi-line transcript string ready to be sent to the LLM.
        """
        if scenario and scenario in SCENARIOS:
            return SCENARIOS[scenario]
        # Default: pick a random scenario
        return random.choice(list(SCENARIOS.values()))

    def get_all_scenarios(self) -> list[str]:
        """Returns the list of available scenario keys."""
        return list(SCENARIOS.keys())


# Singleton instance
mock_transcript_service = MockTranscriptService()
