# Synthetic robustness run (aggregates only)

**These results come from invented, template-generated text. They are NOT clinical validation, and the generator's phrasings can be easier or harder than real speech. No real or challenge data was used and no generated sentence is stored here.**

- seed 20261017, 300 conversations (3872 lines), run time 7.74s
- COACH_CLASSIFIER_DIR set for this process: False (False means the rule tagger ran alone)
- score card ran OK on 300/300 conversations, errors 0

## Flag recall (truth flag lines the engine flagged with the right rule)

| group | detail |
|---|---|
| CHEST|all | {"hit": 40, "total": 48, "recall": 0.8333} |
| CHEST|en | {"hit": 20, "total": 20, "recall": 1.0} |
| CHEST|es | {"hit": 20, "total": 28, "recall": 0.7143} |
| CRISIS|all | {"hit": 60, "total": 60, "recall": 1.0} |
| CRISIS|en | {"hit": 34, "total": 34, "recall": 1.0} |
| CRISIS|es | {"hit": 26, "total": 26, "recall": 1.0} |
| DISTRESS|all | {"hit": 27, "total": 54, "recall": 0.5} |
| DISTRESS|en | {"hit": 10, "total": 23, "recall": 0.4348} |
| DISTRESS|es | {"hit": 17, "total": 31, "recall": 0.5484} |
| SYMPTOM|all | {"hit": 20, "total": 46, "recall": 0.4348} |
| SYMPTOM|en | {"hit": 7, "total": 19, "recall": 0.3684} |
| SYMPTOM|es | {"hit": 13, "total": 27, "recall": 0.4815} |
| all|all | {"hit": 147, "total": 208, "recall": 0.7067} |
| all|en | {"hit": 71, "total": 96, "recall": 0.7396} |
| all|es | {"hit": 76, "total": 112, "recall": 0.6786} |
| base_variant:base|all | {"hit": 74, "total": 112, "recall": 0.6607} |
| base_variant:base|CHEST|all | {"hit": 8, "total": 11, "recall": 0.7273} |
| base_variant:base|CRISIS|all | {"hit": 42, "total": 42, "recall": 1.0} |
| base_variant:base|DISTRESS|all | {"hit": 10, "total": 37, "recall": 0.2703} |
| base_variant:base|SYMPTOM|all | {"hit": 14, "total": 22, "recall": 0.6364} |
| base_variant:order|all | {"hit": 34, "total": 49, "recall": 0.6939} |
| base_variant:order|CHEST|all | {"hit": 18, "total": 23, "recall": 0.7826} |
| base_variant:order|CRISIS|all | {"hit": 10, "total": 10, "recall": 1.0} |
| base_variant:order|SYMPTOM|all | {"hit": 6, "total": 16, "recall": 0.375} |
| base_variant:plural|all | {"hit": 10, "total": 18, "recall": 0.5556} |
| base_variant:plural|CHEST|all | {"hit": 10, "total": 10, "recall": 1.0} |
| base_variant:plural|SYMPTOM|all | {"hit": 0, "total": 8, "recall": 0.0} |
| base_variant:selfneg|all | {"hit": 29, "total": 29, "recall": 1.0} |
| base_variant:selfneg|CHEST|all | {"hit": 4, "total": 4, "recall": 1.0} |
| base_variant:selfneg|CRISIS|all | {"hit": 8, "total": 8, "recall": 1.0} |
| base_variant:selfneg|DISTRESS|all | {"hit": 17, "total": 17, "recall": 1.0} |
| variant:base|all | {"hit": 27, "total": 33, "recall": 0.8182} |
| variant:noisy|all | {"hit": 95, "total": 143, "recall": 0.6643} |
| variant:order|all | {"hit": 13, "total": 16, "recall": 0.8125} |
| variant:plural|all | {"hit": 5, "total": 9, "recall": 0.5556} |
| variant:selfneg|all | {"hit": 7, "total": 7, "recall": 1.0} |

## Flag precision by rule

| group | detail |
|---|---|
| F-CHEST|all | {"tp": 40, "predicted": 40, "precision": 1.0} |
| F-CHEST|en | {"tp": 20, "predicted": 20, "precision": 1.0} |
| F-CHEST|es | {"tp": 20, "predicted": 20, "precision": 1.0} |
| F-CRISIS|all | {"tp": 60, "predicted": 60, "precision": 1.0} |
| F-CRISIS|en | {"tp": 34, "predicted": 34, "precision": 1.0} |
| F-CRISIS|es | {"tp": 26, "predicted": 26, "precision": 1.0} |
| F-DISTRESS|all | {"tp": 27, "predicted": 62, "precision": 0.4355} |
| F-DISTRESS|en | {"tp": 10, "predicted": 20, "precision": 0.5} |
| F-DISTRESS|es | {"tp": 17, "predicted": 42, "precision": 0.4048} |
| F-SYMPTOM|all | {"tp": 20, "predicted": 25, "precision": 0.8} |
| F-SYMPTOM|en | {"tp": 7, "predicted": 7, "precision": 1.0} |
| F-SYMPTOM|es | {"tp": 13, "predicted": 18, "precision": 0.7222} |

## False-alarm rate (decoy and neutral lines wrongly flagged)

| group | detail |
|---|---|
| BENIGN|all | {"flagged": 0, "total": 90, "rate": 0.0} |
| BENIGN|en | {"flagged": 0, "total": 49, "rate": 0.0} |
| BENIGN|es | {"flagged": 0, "total": 41, "rate": 0.0} |
| NEG|all | {"flagged": 14, "total": 177, "rate": 0.0791} |
| NEG|en | {"flagged": 0, "total": 90, "rate": 0.0} |
| NEG|es | {"flagged": 14, "total": 87, "rate": 0.1609} |
| NEUTRAL|all | {"flagged": 0, "total": 1289, "rate": 0.0} |
| NEUTRAL|en | {"flagged": 0, "total": 633, "rate": 0.0} |
| NEUTRAL|es | {"flagged": 0, "total": 656, "rate": 0.0} |
| OTHER|all | {"flagged": 0, "total": 93, "rate": 0.0} |
| OTHER|en | {"flagged": 0, "total": 46, "rate": 0.0} |
| OTHER|es | {"flagged": 0, "total": 47, "rate": 0.0} |
| PAST|all | {"flagged": 21, "total": 79, "rate": 0.2658} |
| PAST|en | {"flagged": 10, "total": 40, "rate": 0.25} |
| PAST|es | {"flagged": 11, "total": 39, "rate": 0.2821} |
| all|all | {"flagged": 35, "total": 1728, "rate": 0.0203} |
| all|en | {"flagged": 10, "total": 858, "rate": 0.0117} |
| all|es | {"flagged": 25, "total": 870, "rate": 0.0287} |

## Coach-move tag recall

| group | detail |
|---|---|
| affirm|all | {"hit": 180, "total": 228, "recall": 0.7895} |
| affirm|en | {"hit": 64, "total": 112, "recall": 0.5714} |
| affirm|es | {"hit": 116, "total": 116, "recall": 1.0} |
| all|all | {"hit": 744, "total": 1936, "recall": 0.3843} |
| all|en | {"hit": 372, "total": 954, "recall": 0.3899} |
| all|es | {"hit": 372, "total": 982, "recall": 0.3788} |
| ask_permission|all | {"hit": 132, "total": 269, "recall": 0.4907} |
| ask_permission|en | {"hit": 62, "total": 137, "recall": 0.4526} |
| ask_permission|es | {"hit": 70, "total": 132, "recall": 0.5303} |
| closed_question|all | {"hit": 56, "total": 219, "recall": 0.2557} |
| closed_question|en | {"hit": 56, "total": 96, "recall": 0.5833} |
| closed_question|es | {"hit": 0, "total": 123, "recall": 0.0} |
| complex_reflection|all | {"hit": 0, "total": 244, "recall": 0.0} |
| complex_reflection|en | {"hit": 0, "total": 131, "recall": 0.0} |
| complex_reflection|es | {"hit": 0, "total": 113, "recall": 0.0} |
| give_information|all | {"hit": 0, "total": 261, "recall": 0.0} |
| give_information|en | {"hit": 0, "total": 109, "recall": 0.0} |
| give_information|es | {"hit": 0, "total": 152, "recall": 0.0} |
| open_question|all | {"hit": 134, "total": 241, "recall": 0.556} |
| open_question|en | {"hit": 65, "total": 129, "recall": 0.5039} |
| open_question|es | {"hit": 69, "total": 112, "recall": 0.6161} |
| seek_collaboration|all | {"hit": 229, "total": 229, "recall": 1.0} |
| seek_collaboration|en | {"hit": 112, "total": 112, "recall": 1.0} |
| seek_collaboration|es | {"hit": 117, "total": 117, "recall": 1.0} |
| simple_reflection|all | {"hit": 13, "total": 245, "recall": 0.0531} |
| simple_reflection|en | {"hit": 13, "total": 128, "recall": 0.1016} |
| simple_reflection|es | {"hit": 0, "total": 117, "recall": 0.0} |

## Missed template IDs (id|language, count; FALSE-ALARM: ids are decoys that wrongly flagged)

- FALSE-ALARM:NEG-04|es: 14
- FALSE-ALARM:PAST-02|es: 11
- FALSE-ALARM:PAST-02|en: 10
- DISTRESS-04|es: 8
- DISTRESS-03|en: 8
- DISTRESS-03|es: 6
- SYMPTOM-06|es: 6
- SYMPTOM-08|en: 6
- DISTRESS-04|en: 5
- CHEST-04|es: 5
- SYMPTOM-02|en: 4
- SYMPTOM-02|es: 4
- CHEST-07|es: 3
- SYMPTOM-07|en: 2
- SYMPTOM-07|es: 2
- SYMPTOM-08|es: 2

## Plural / word-order variant misses by flag rule

- F-CHEST|order: 5
- F-SYMPTOM|order: 10
- F-SYMPTOM|plural: 8
