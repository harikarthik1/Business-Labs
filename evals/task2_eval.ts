import { SYNTHETIC_EMAIL_FIXTURES } from "../task2_inbox_agent/src/fixtures";
import { emailClassifier } from "../task2_inbox_agent/src/classifier";
import { draftGenerator } from "../task2_inbox_agent/src/draftGenerator";
import { autonomyEngine, calculateTextSimilarity } from "../task2_inbox_agent/src/autonomy";

export async function runTask2Eval() {
  console.log("\n========================================================");
  console.log(`RUNNING TASK 2 EVALUATION (${SYNTHETIC_EMAIL_FIXTURES.length} fixtures)`);
  console.log("========================================================\n");

  let correctClassifications = 0;
  let validDraftCount = 0;
  let totalLatency = 0;
  const results = [];

  for (const fixture of SYNTHETIC_EMAIL_FIXTURES) {
    const startTime = Date.now();
    const classification = emailClassifier.classify(fixture.subject, fixture.body);
    const isCatCorrect = classification.category === fixture.category;
    if (isCatCorrect) correctClassifications++;

    const draft = await draftGenerator.generateDraft(
      fixture.id,
      fixture.sender_name,
      fixture.subject,
      fixture.body,
      fixture.category
    );

    const elapsed = Date.now() - startTime;
    totalLatency += elapsed;

    // Validate draft quality criteria
    const hasSalutation = draft.original_draft.includes(fixture.sender_name);
    const hasClosing = draft.original_draft.includes("regards") || draft.original_draft.includes("Sincerely");
    const hasSufficientLength = draft.original_draft.split(" ").length >= 25;
    const isDraftValid = hasSalutation && hasClosing && hasSufficientLength;
    if (isDraftValid) validDraftCount++;

    results.push({
      id: fixture.id,
      category: fixture.category,
      classified_category: classification.category,
      category_match: isCatCorrect,
      draft_valid: isDraftValid,
      confidence: draft.confidence,
      sources_cited: draft.sources_used.length,
      latency_ms: elapsed,
    });

    const statusStr = isCatCorrect && isDraftValid ? "PASS" : "WARN";
    console.log(`[${statusStr}] ${fixture.id} (${fixture.category}): Match=${isCatCorrect}, Quality=${isDraftValid}, Citations=${draft.sources_used.length}`);
  }

  // Evaluate 20-streak Autonomy Gate
  const engine = new autonomyEngine.constructor();
  let streakGranted = false;
  let streakRevoked = false;

  for (let i = 1; i <= 20; i++) {
    const res = engine.evaluateReview(`eval_streak_${i}`, "how_to", "Draft text", "Draft text");
    if (i === 20 && res.autonomous_eligible) {
      streakGranted = true;
    }
  }

  // Break streak with an edit
  const breakRes = engine.evaluateReview("eval_streak_break", "how_to", "Draft text", "Edited draft text with revisions");
  if (!breakRes.autonomous_eligible && breakRes.consecutive_after === 0) {
    streakRevoked = true;
  }

  const classAccuracy = (correctClassifications / SYNTHETIC_EMAIL_FIXTURES.length) * 100;
  const draftQualityRate = (validDraftCount / SYNTHETIC_EMAIL_FIXTURES.length) * 100;
  const avgLatency = Math.round(totalLatency / SYNTHETIC_EMAIL_FIXTURES.length);

  console.log("\n--------------------------------------------------------");
  console.log("TASK 2 EVALUATION SUMMARY:");
  console.log(`• Classification Accuracy: ${classAccuracy.toFixed(1)}% (${correctClassifications}/${SYNTHETIC_EMAIL_FIXTURES.length})`);
  console.log(`• Draft Quality Pass Rate: ${draftQualityRate.toFixed(1)}% (${validDraftCount}/${SYNTHETIC_EMAIL_FIXTURES.length})`);
  console.log(`• 20-Streak Autonomy Qualification Verified: ${streakGranted ? "PASS" : "FAIL"}`);
  console.log(`• Edit Streak Revocation Verified: ${streakRevoked ? "PASS" : "FAIL"}`);
  console.log(`• Average Draft Latency: ${avgLatency} ms`);
  console.log("--------------------------------------------------------\n");

  return {
    total_fixtures: SYNTHETIC_EMAIL_FIXTURES.length,
    classification_accuracy: classAccuracy,
    draft_quality_rate: draftQualityRate,
    autonomy_qualification_verified: streakGranted,
    autonomy_revocation_verified: streakRevoked,
    average_latency_ms: avgLatency,
    results,
  };
}

if (require.main === module) {
  runTask2Eval().catch(console.error);
}
