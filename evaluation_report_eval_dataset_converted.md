# RAG Evaluation Report
    
**Dataset:** eval_dataset_converted.json
**Total Samples:** 7
**Average Correctness Score (1-5):** 2.86
**Retrieval Hit Rate:** 71.43%

## Q: Требуется продлить срок действия договора имущественного найма (аренды) государственного имущества, однако заявка была подана за 7 дней до окончания срока действия договора имущественного найма (аренды). Как продлить этот действующий договор аренды?
- **Score:** 5/5
- **Retrieval Hit:** True (Target: v1500010467.02-10-2025.rus.docx)
- **Explanation:** The Agent Answer accurately covers all key elements from the Ground Truth, including the 10-working-day requirement for the application (noting the 7-day submission as non-compliant), the procedure for additional agreements, term limits (up to 6 years generally, 25 for investments), electronic format via the web portal, and no refusal from the balance holder. It matches factually without omissions or errors.
- **Latency:** 13.68s
---
## Q: Какие критерии есть при передаче гос.имущества?
- **Score:** 4/5
- **Retrieval Hit:** False (Target: g25nt000075.04-08-2025.rus.docx)
- **Explanation:** The Agent Answer accurately captures the core criteria from the Ground Truth for transferring state property between types of state ownership, including economic feasibility, need within natural norms (Article 70 of the Budget Code), targeted use, and financial provision. However, it deducts a point for adding extraneous details on property acquisition via donation contracts, which are not part of the Ground Truth and could introduce minor scope creep, though factually correct in context.
- **Latency:** 15.00s
---
## Q: По правилам приобретения государством прав на имущество по договору дарения при каких случаях не производится оценка имущества?
- **Score:** 3/5
- **Retrieval Hit:** True (Target: p1100001103.12-04-2023.rus.docx)
- **Explanation:** The Agent Answer is factually correct for the points it covers (report on evaluation, declaration of compliance, and nominal valuation of money/securities), but it is incomplete as it omits several key cases from the Ground Truth, such as copies of land documents, acceptance acts, owner's decisions on transfer, and geodetic surveys.
- **Latency:** 7.80s
---
## Q: Приведи процедуру по субаренде в общем случае и подробно
- **Score:** 1/5
- **Retrieval Hit:** True (Target: v1500010467.02-10-2025.rus.docx)
- **Explanation:** The Agent Answer incorrectly states that the information is absent from the normative acts, while the Ground Truth provides detailed procedures for subleasing, including requirements for written permission, application process, and decision timelines, directly contradicting the agent's claim.
- **Latency:** 5.07s
---
## Q: Дайте разъяснения по срокам проведения тендера на аренду, так как на объект предложенный балансодержателем в имущественный наем (аренду) было подано два заявления от разных кандидатов по аренде
- **Score:** 1/5
- **Retrieval Hit:** False (Target: v1500010467.02-10-2025.rus.docx)
- **Explanation:** The Agent Answer seeks clarification on the type of rental instead of providing the requested explanations on tender timelines and definitions from the Ground Truth, making it factually incorrect and non-responsive.
- **Latency:** 0.88s
---
## Q: Существуют ли какие-либо базовые ставки по аренде?
- **Score:** 2/5
- **Retrieval Hit:** True (Target: v1500010467.02-10-2025.rus.docx)
- **Explanation:** The Agent Answer provides formulas and details for calculating rental payments based on balance value and amortization for general state property, but it does not address or mention base rates or coefficients for non-residential premises as specified in the Ground Truth, which refers to specific factors like building type, location, and tenant activity detailed in Appendix 5. This makes it factually incomplete and mismatched to the expected content.
- **Latency:** 9.96s
---
## Q: Какова процедура списания биологических активов?
- **Score:** 4/5
- **Retrieval Hit:** True (Target: 20251219 - Алгоритм Отдела коммунального имущества)
- **Explanation:** The Agent Answer accurately lists all the key documents from the Ground Truth (приказ, протокол, акт, ветеринарный паспорт, заключение ветеринара) as part of the required submission for approval. It expands on the full procedure with additional steps and references, which are factually consistent and do not contradict the Ground Truth, though it goes beyond the concise list provided.
- **Latency:** 12.78s
---
