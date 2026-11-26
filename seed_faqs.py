import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'CRM.settings')
django.setup()

from partneracademy.models import PartnerFAQ

FAQS_DATA = [
    # =========================================================================
    # PARTNER (Partner Admin / Partner Organization)
    # =========================================================================
    {
        "category": "Application",
        "question": "FAQ 1: How do I check the approval status of our Partner Application?",
        "short_desc": "Tracking application submission and review stages.",
        "order": 1,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": [],
        "answer": """To track your partner application:
1. Log in to the Partner Portal and check your "Applications" tab.
2. The status badge will display either "Under Review", "Action Required", or "Approved".
3. If additional business details are needed, your assigned Partner Manager will leave a note directly in your application dashboard.
4. Once approved, you will be invited to complete KYC Verification."""
    },
    {
        "category": "KYC Verification",
        "question": "FAQ 2: What documents are required to complete Partner KYC verification?",
        "short_desc": "Business proof, tax credentials, and bank account verification.",
        "order": 2,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": [],
        "answer": """To complete KYC verification:
1. Go to "KYC Verification" in the sidebar.
2. Upload clear scanned copies of:
   - Certificate of Incorporation / Business Registration
   - Company PAN Card
   - GSTIN Certificate
   - Cancelled Cheque or Bank Statement (for commission payouts)
3. Confirm your registered business address and authorized signatory details.
4. Click "Submit for Verification". Review typically takes 24 to 48 business hours."""
    },
    {
        "category": "Agreement",
        "question": "FAQ 3: How do I review and digitally sign the Partner Agreement?",
        "short_desc": "Agreement review, OTP verification, and executed copy download.",
        "order": 3,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": [],
        "answer": """Once your KYC is approved:
1. Navigate to "Agreements" in the sidebar.
2. Click "View Agreement" to read the partnership terms, tier level, and commission percentages.
3. Click "Sign Agreement" to complete the digital signing using your registered email and mobile OTP.
4. A signed copy is immediately archived and remains accessible for download anytime under your Agreements tab."""
    },
    {
        "category": "My Leads",
        "question": "FAQ 4: How do I submit and register a new prospective client lead?",
        "short_desc": "Deal registration, conflict protection, and lead timeline.",
        "order": 4,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": ["Sales"],
        "answer": """To register a new lead:
1. Go to "My Leads" in the sidebar and click "+ Add New Lead".
2. Fill in the client's Company Name, Contact Person, Phone, Email, and the Target Product (CRM, Retail, People, IT).
3. Select the estimated deal size and expected closure date.
4. Click "Submit Lead". 

Registered leads are protected for 90 days, ensuring your partner organization is exclusively credited for the deal."""
    },
    {
        "category": "My Deals",
        "question": "FAQ 5: How do I track deal progress and convert a lead into a closed deal?",
        "short_desc": "Deal pipeline stages from negotiation to contract signing.",
        "order": 5,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": ["Sales"],
        "answer": """In your "My Deals" workspace:
1. View your active deal pipeline across stages: Qualification -> Demo / Proposal -> Negotiation -> Closed Won.
2. Update the deal status as negotiations progress.
3. When the customer agrees to purchase, mark the deal as "Closed Won" and attach the customer purchase order to trigger customer provisioning."""
    },
    {
        "category": "My Customers",
        "question": "FAQ 6: Where can I see all active customer accounts assigned to our organization?",
        "short_desc": "Managing assigned clients, license tiers, and renewal dates.",
        "order": 6,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": [],
        "answer": """Navigate to "My Customers" in your sidebar to:
- View all live customer organizations linked to your partner account.
- Check their active product suites, user seat counts, and subscription renewal dates.
- Access direct support history and assign implementation consultants from your team."""
    },
    {
        "category": "My Commissions",
        "question": "FAQ 7: How are partner commissions calculated and when are payouts credited?",
        "short_desc": "Earnings calculation, GST tax invoice submission, and payout dates.",
        "order": 7,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": [],
        "answer": """Partner commission process:
1. Commission Calculation: You earn pre-agreed commission percentages on all customer software subscriptions and recurring renewals.
2. Monthly Lock: Commissions for the current month lock on the final calendar day.
3. Invoice Submission: On the 1st of each month, go to "My Commissions", click "Generate Statement", and upload your signed GST Tax Invoice.
4. Bank Transfer: Payouts are credited directly to your verified KYC bank account by the 10th of every month."""
    },
    {
        "category": "Daily Work Update",
        "question": "FAQ 8: How do I submit our partner daily activity and work updates?",
        "short_desc": "Logging client meetings, demos, implementation milestones, and notes.",
        "order": 8,
        "show_partner": True,
        "show_team": False,
        "show_user": False,
        "roles": ["HR"],
        "answer": """To submit your daily work update:
1. Go to "Daily Work Update" in the sidebar.
2. Click "+ New Work Update".
3. Select the relevant Date, Customer or Lead name, and Activity Type (Client Demo, Requirement Gathering, Implementation, Training).
4. Enter a summary of tasks completed, next steps, and hours spent.
5. Click "Save Update" to record your activity log for governance review."""
    },
    {
        "category": "Training Academy",
        "question": "FAQ 9: How do partner staff access the Training Academy courses?",
        "short_desc": "Video walkthroughs, module navigation, and progress tracking.",
        "order": 9,
        "show_partner": True,
        "show_team": True,
        "show_user": False,
        "roles": [],
        "answer": """To access training:
1. Click "Training Academy" in your sidebar.
2. Select your target product suite (CRM, Retail, People, IT, Education, etc.).
3. Choose a module and watch video walkthroughs step-by-step.
4. Your video completion percentage is saved in real-time. Completing all modules is required to unlock certification assessments."""
    },
    {
        "category": "Support Tickets",
        "question": "FAQ 10: How do I raise a support ticket for customer implementation or portal issues?",
        "short_desc": "Ticket creation, priority selection, and tracking engineering resolution.",
        "order": 10,
        "show_partner": True,
        "show_team": True,
        "show_user": False,
        "roles": [],
        "answer": """If you or your client need support:
1. Go to "Support Tickets" in your sidebar and click "+ Open Ticket".
2. Choose the Ticket Category (Implementation, Technical Bug, Commission Query, Billing).
3. Set the Priority (Critical, High, Medium, Low).
4. Provide details and attach error screenshots or log files.
5. Click "Submit". Our technical operations team will respond within the SLA window."""
    },

    # =========================================================================
    # MANAGEMENT USERS (Global Partner Head, Country Manager, Regional Managers)
    # =========================================================================
    {
        "category": "Leads Management",
        "question": "FAQ 11: How do management users review, approve, and assign partner leads?",
        "short_desc": "Lead validation, duplicate check, and regional assignment.",
        "order": 11,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["Sales", "GLOBAL_PARTNER_HEAD", "COUNTRY_MANAGER"],
        "answer": """To manage partner leads:
1. Open "Lead Management" -> "Leads".
2. Review newly submitted leads from partners across your region.
3. Verify there are no duplicate accounts or channel conflicts.
4. Click "Approve Lead" to grant the 90-day protection window, or route the lead to a specific regional partner."""
    },
    {
        "category": "Partner Applications",
        "question": "FAQ 12: How do governance managers review and approve new partner applications?",
        "short_desc": "Company background check, tier assignment, and status updates.",
        "order": 12,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["GLOBAL_PARTNER_HEAD", "COUNTRY_MANAGER", "REGIONAL_MANAGER"],
        "answer": """To review incoming applications:
1. Go to "Partner Management" -> "Applications".
2. Open the pending application to inspect the applicant's company profile, years in business, and technical capabilities.
3. Assign a partnership tier (e.g. Silver, Gold, Platinum).
4. Click "Approve Application" to invite them to the KYC verification stage."""
    },
    {
        "category": "KYC Approvals",
        "question": "FAQ 13: How do KYC Managers verify business documents and approve partner KYC?",
        "short_desc": "Validating GST, PAN, and banking proofs.",
        "order": 13,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["KYC_MANAGER", "COUNTRY_MANAGER"],
        "answer": """To review partner KYC submissions:
1. Navigate to "KYC Verification" under Partner Management.
2. Open the pending submission to inspect uploaded GST, PAN, and Bank Cheque documents.
3. Validate tax numbers against official government records.
4. Click "Verify KYC" to approve, or "Request Re-upload" with specific feedback if documents are blurry or incomplete."""
    },
    {
        "category": "Agreements Management",
        "question": "FAQ 14: How are partner agreements generated and tracked across regions?",
        "short_desc": "Issuing master agreements, digital signatures, and compliance tracking.",
        "order": 14,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["GLOBAL_PARTNER_HEAD", "COUNTRY_MANAGER"],
        "answer": """Under the "Agreements" module:
1. Once KYC is verified, generate the standard regional partnership agreement.
2. Set custom commercial clauses or commission addendums if approved.
3. Dispatch the agreement for partner digital signature.
4. Track real-time signing status (Draft -> Sent -> Signed)."""
    },
    {
        "category": "Assign Customers",
        "question": "FAQ 15: How do managers allocate customer accounts to verified partners?",
        "short_desc": "Client assignment, onboarding handover, and account re-allocation.",
        "order": 15,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["COUNTRY_MANAGER", "GLOBAL_PARTNER_HEAD"],
        "answer": """To assign a customer organization to a partner:
1. Go to "Assign Customers" in the sidebar.
2. Select the customer organization and click "Assign Partner".
3. Choose the certified partner organization from the dropdown list.
4. Confirm the assignment. The partner will immediately see the client in their "My Customers" tab."""
    },
    {
        "category": "Upload Videos",
        "question": "FAQ 16: How do Training Managers upload product training videos and configure modules?",
        "short_desc": "Video file uploads, product suite selection, and curriculum publishing.",
        "order": 16,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["TRAINING_MANAGER", "GLOBAL_PARTNER_HEAD"],
        "answer": """To publish curriculum videos:
1. Navigate to "Upload Videos" in the sidebar.
2. Select the Target Product Suite and Module Topic (or click "+ Custom Topic").
3. Enter the Video Title, Sequence Number, and Description.
4. Upload the video file (MP4/WebM) and custom thumbnail image.
5. Click "Publish Video". The video is instantly added to the partner Training Academy curriculum."""
    },
    {
        "category": "Upload Technical Documentation",
        "question": "FAQ 17: How do managers create, upload, and publish technical documentation and runbooks?",
        "short_desc": "Document Code generation, schema specifications, and Cloudflare R2 upload.",
        "order": 17,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["TECHNICAL_MANAGER", "GLOBAL_PARTNER_HEAD"],
        "answer": """To publish technical documentation:
1. Go to "Upload Technical Documentation" in your sidebar and click "+ Upload Document".
2. Select the Product Suite and Module. The unique Document Code (e.g. PCRM-ARCH-01) and Title auto-populate.
3. Select or type the Document Type (e.g. API Documentation, Database Schema) and Category.
4. Attach the technical specification file (PDF, DOCX, ZIP, JSON, SQL).
5. Click "Publish Technical Document". The document is published under strict read-only governance for Technical Managers."""
    },
    {
        "category": "Certifications",
        "question": "FAQ 18: How do managers review partner assessment scores and issue official certificates?",
        "short_desc": "Scorecard review, certificate authorization, and badge allocation.",
        "order": 18,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["TRAINING_MANAGER", "GLOBAL_PARTNER_HEAD"],
        "answer": """In the "Certification" module:
1. Review partner team members who have completed 100% video hours and scored >= 80% on the final assessment.
2. Verify their practical assessment submission if applicable.
3. Click "Approve & Issue Certificate". The system generates a cryptographically signed digital certificate and updates the partner organization's certification badge."""
    },
    {
        "category": "Daily Work Updates",
        "question": "FAQ 19: How do Country and Regional Managers audit daily work logs from partners?",
        "short_desc": "Monitoring partner activities, customer visits, and implementation hours.",
        "order": 19,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["HR", "COUNTRY_MANAGER", "REGIONAL_MANAGER"],
        "answer": """To review daily logs:
1. Navigate to "Daily Work Update" under management tools.
2. Filter logs by Partner Organization, Date Range, or Customer Name.
3. Review tasks logged, customer interactions, and hours spent.
4. Add internal governance remarks or flag items requiring follow-up."""
    },
    {
        "category": "Support Tickets",
        "question": "FAQ 20: How do managers triage, assign, and resolve partner support tickets?",
        "short_desc": "SLA tracking, engineering assignment, and status closure.",
        "order": 20,
        "show_partner": False,
        "show_team": False,
        "show_user": True,
        "roles": ["TECHNICAL_MANAGER", "GLOBAL_PARTNER_HEAD", "COUNTRY_MANAGER"],
        "answer": """Under "Service" -> "Tickets":
1. View all open partner tickets ranked by priority and SLA timer.
2. Assign tickets to specific technical leads or implementation engineers.
3. Post resolution notes or requests for further logs directly in the ticket thread.
4. Mark the ticket "Resolved" once confirmed with the partner."""
    },

    # =========================================================================
    # PARTNER TEAM MEMBERS (Consultants, Engineers, Trainees)
    # =========================================================================
    {
        "category": "Certification",
        "question": "FAQ 21: How do team members take the exam and receive their Certified Specialist badge?",
        "short_desc": "Online assessment rules, 80% passing threshold, and PDF certificate download.",
        "order": 21,
        "show_partner": False,
        "show_team": True,
        "show_user": False,
        "roles": [],
        "answer": """Once all module videos are marked 100% complete:
1. Go to "Certification" under the Academy menu.
2. Click "Start Certification Exam".
3. Answer the multiple-choice questions within the allotted time limit (minimum passing score is 80%).
4. Upon passing, your official Pegatto Certified Specialist Certificate is generated and accessible on your profile for download."""
    },
    {
        "category": "My Profile",
        "question": "FAQ 22: Where can team members view their active role, certifications, and account settings?",
        "short_desc": "Viewing personal badges, resetting passwords, and updating contact details.",
        "order": 22,
        "show_partner": False,
        "show_team": True,
        "show_user": False,
        "roles": [],
        "answer": """Go to "My Profile" in the top-left sidebar to:
- View your active partner organization affiliation and system role.
- View and download all earned Pegatto Product Certification badges.
- Update your contact phone number, job title, and password security credentials."""
    }
]

print(f"Updating table 'PartnerFAQ' with {len(FAQS_DATA)} FAQs with Show_To_* and Visible_User_Roles...")

PartnerFAQ.objects.all().delete()

for idx, item in enumerate(FAQS_DATA, start=1):
    faq_id = f"PFQ{str(idx).zfill(9)}"
    faq = PartnerFAQ.objects.create(
        PartnerFAQ_Id=faq_id,
        Category_Name=item["category"],
        Question=item["question"],
        Answer=item["answer"],
        Short_Description=item["short_desc"],
        Display_Order=item["order"],
        Is_Active=True,
        Is_Deleted=False,
        Show_To_Partner=item.get("show_partner", True),
        Show_To_Team_Member=item.get("show_team", False),
        Show_To_User=item.get("show_user", False),
        Visible_User_Roles=item.get("roles", [])
    )
    print(f"[{idx}/{len(FAQS_DATA)}] Created {faq.PartnerFAQ_Id} | P:{faq.Show_To_Partner} TM:{faq.Show_To_Team_Member} U:{faq.Show_To_User} | Roles:{faq.Visible_User_Roles} | {faq.Question[:45]}...")

print("\nSUCCESS: All 22 FAQs seeded with 'FAQ 1: ...' and Visible_User_Roles=['HR', 'Sales', ...]")
