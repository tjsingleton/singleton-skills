---
name: delivery-codes
description: >
  Find current Uber Eats and DoorDash promo codes in the user's Gmail and add
  new valid offers to Apple Notes. Use when asked to scan email and maintain a
  delivery-code note. Don't use for public coupon searches or placing orders.
argument-hint: '[note-title:"Delivery Codes"] [as-of:YYYY-MM-DD]'
license: MIT
---

# Delivery Codes

> **Quick usage:**
> ```text
> delivery-codes
> delivery-codes note-title:"Delivery Codes"
> delivery-codes as-of:2026-09-12
> ```

Use the active host's current local date unless the user explicitly supplies an
`as-of` date. The default note title is `Delivery Codes`. Parse any overrides
from the active host's invocation arguments without requiring them.

## Workflow

1. Search the user's Gmail through the Gmail connector for recent messages from
   Uber Eats (including `UberEats` and `Uber Eats`) and DoorDash that mention a
   promo, promotion, discount, offer, or code. Search each merchant separately
   and broaden the date range only when the initial results do not cover offers
   that could still be active. Do not substitute public coupon sites: these
   offers may be account-specific.
2. Open plausible messages and read the message body and offer terms. Do not
   decide from subject lines or snippets alone. Record each candidate's exact
   code, merchant, benefit, expiration date and time, minimum spend, eligible
   order or store type, use limit, account/new-customer requirement, delivery
   versus pickup restriction, and region when stated.
3. Evaluate every candidate against the effective local date:
   - Exclude an offer whose stated expiration is before that date.
   - Treat an offer that expires on the effective date as active through that
     day unless the message gives an earlier time or timezone.
   - Do not invent a year, timezone, region, or eligibility rule. If the
     expiration cannot be established confidently, report it as uncertain and
     do not add it automatically.
   - Treat phrases such as "sent just for you," "your account," or similar
     wording as a direct-recipient restriction. Preserve that restriction in
     the note rather than presenting the code as generally reusable.
   - Preserve geographic restrictions. Do not add a code whose stated region
     clearly excludes the user's region; if the user's region is unknown,
     record the restriction and flag eligibility as uncertain.
4. Open Apple Notes using computer use and locate the note whose title exactly
   matches the requested title. Read its complete current contents before any
   edit. If multiple notes match or the note cannot be found, stop and report
   the ambiguity instead of creating or editing a different note.
5. Deduplicate candidate codes against the note and against one another using a
   case-insensitive, whitespace-trimmed comparison. When the same code appears
   in multiple emails, keep the clearest current terms and the latest supported
   expiration. Do not add a second copy merely because capitalization or offer
   wording differs.
6. Append only confirmed, currently valid, non-duplicate codes. Keep each entry
   concise and scannable: `CODE — offer; expires DATE; key restrictions`.
   Include only terms that affect redemption, especially minimum spend,
   eligible order type, use limit, direct-recipient/account limitation, and
   region. Preserve the note's existing organization and do not delete expired
   or unrelated entries unless the user explicitly asks for cleanup.
7. Save the note, then re-read its contents through computer use. Confirm each
   intended code appears exactly once with the correct expiration and material
   restrictions. A completed edit action without this readback is not proof of
   success.

## Report

State which codes were added, which candidates were skipped as expired,
duplicate, region-ineligible, or uncertain, the effective date used, and that
the final note was re-read successfully. Never expose unrelated email content.

## Boundaries

- Gmail access is read-only for this workflow; do not archive, label, delete,
  reply to, or otherwise mutate messages.
- The Apple Notes edit is limited to the exact requested note.
- Searching for and recording codes does not authorize applying a code,
  changing an account, or placing an order.
