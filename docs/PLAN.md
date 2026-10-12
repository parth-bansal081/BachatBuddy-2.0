# Build plan (Oct 10 - Oct 28 internal deadline; hackathon deadline Oct 30, 10:00 AM PDT = 10:30 PM IST)

Stack decision: **Vite + React Router** (not Next.js) so the working Setu frontend files can be copied unchanged.

| Phase | Dates | Goal | Done when |
|---|---|---|---|
| 0 Foundation | Oct 10-11 | New repo and frontend on the SAME Vercel domain and the SAME live backend; Setu files copied unchanged; Token Factory call works | Golden path passes on the new frontend AND one Nemotron reply received |
| 1 Data spine | Oct 12-14 | Setu data -> queue -> worker -> normalized transactions (regex shield, merchant cache, Nemotron Nano) | Sandbox data flows end to end; accuracy baseline measured on fixtures |
| 2 Money brain | Oct 15-19 | Policy schema, compiler, deterministic rule engine, backtester | A plain-language policy yields a backtest on sandbox history |
| 3 UI (parallel) | Oct 13-19 | New design system, app shell, onboarding, ledger, envelopes, bills, review queue | All screens work on real data |
| 4 Agent loop | Oct 20-23 | Approval cards, UPI deep links, memory, tool-calling chat, Tavily | A payment event triggers a proposed action the user approves |
| 5 Hero + polish | Oct 24-26 | The signature demo moment, mobile, empty/error states | Demo runs start to finish without help |
| 6 Ship | Oct 27-28 | Eval numbers, README, 3-minute video, feedback form, submit | Submitted with buffer |

Cut order if behind: Tavily, then memory, then Hinglish input.

## Golden path (run after EVERY merge)
1. Sign in. 2. Dashboard -> "Link Bank Account" -> "Proceed to Link".
3. Setu/Onemoney screen: phone 9999999999, OTP 123456, approve.
4. Redirected back to the app. 5. Accounts and transactions appear on the dashboard.
