import json
from pathlib import Path

LAB=Path(__file__).parents[1]; OUT=LAB/'results'/'v0.3.1-semantic-audit'; OUT.mkdir(exist_ok=True)
# Independent bounded review: all other replies restate supplied evidence or make no material factual assertion.
UNSUPPORTED={
 'baseline':{'C03':'States the charge is a post-cancellation fee; supplied policy requires review but does not establish a fee.'},
 'candidate':{'C01':'Introduces an account manager not present in supplied evidence.','C09':'Requests an MFA device serial number not supported by the supplied facts.','C13':'Claims access to API logs, which is not supplied.','C15':'Claims colleague coordination/escalation authority not supplied.','C23':'Claims policy restrictions preventing cancellation, not supplied.','C24':'Promises dark mode in the next update, not supplied.','C25':'Promises implementation of bulk export, not supplied.','C27':'States a settings capability not supplied.','C28':'States website navigation and invoice-download steps not supplied.'}}
def rows(path): return [json.loads(x) for x in path.read_text().splitlines()]
def main():
 records=[]
 for config,root in [('baseline',LAB/'results/v0.3/execution-clean-01'),('candidate',LAB/'results/v0.3/execution-candidate-clean-02')]:
  gen={x['case_id']:x for x in rows(root/f'{config}_generation.jsonl')}; sem={x['case_id']:x for x in rows(root/f'{config}_semantic.jsonl')}
  for cid in sorted(gen):
   human='unsupported' if cid in UNSUPPORTED[config] else 'supported'; judge=sem[cid]
   if not judge.get('available'): agreement='judge_unavailable'
   elif judge['supported'] and human=='supported': agreement='true_negative'
   elif not judge['supported'] and human=='unsupported': agreement='true_positive'
   elif not judge['supported']: agreement='false_positive'
   else: agreement='false_negative'
   records.append({'case_id':cid,'configuration':config,'customer_reply':gen[cid]['parsed_structured_output']['customer_reply'],'semantic_judge_supported':judge.get('supported'),'judge_unsupported_claims':judge.get('unsupported_claims',[]),'human_audit_decision':human,'human_unsupported_claims':[UNSUPPORTED[config][cid]] if cid in UNSUPPORTED[config] else [],'evaluator_agreement':agreement,'rationale':'Missing evidence: '+UNSUPPORTED[config][cid] if cid in UNSUPPORTED[config] else 'Reply is grounded in supplied customer facts or makes no material factual assertion.'})
 (OUT/'semantic_audit.jsonl').write_text(''.join(json.dumps(x)+'\n' for x in records))
 def summary(config):
  x=[r for r in records if r['configuration']==config]; return {'outputs':len(x),'human_supported_rate':sum(r['human_audit_decision']=='supported' for r in x)/len(x),'judge_human_agreement':sum(r['evaluator_agreement'] in ('true_positive','true_negative') for r in x)/len(x),'false_positives':sum(r['evaluator_agreement']=='false_positive' for r in x),'false_negatives':sum(r['evaluator_agreement']=='false_negative' for r in x),'judge_unavailable':sum(r['evaluator_agreement']=='judge_unavailable' for r in x)}
 result={'baseline':summary('baseline'),'candidate':summary('candidate'),'combined':{'outputs':60,'false_positives':sum(r['evaluator_agreement']=='false_positive' for r in records),'false_negatives':sum(r['evaluator_agreement']=='false_negative' for r in records),'unavailable':sum(r['evaluator_agreement']=='judge_unavailable' for r in records)}}
 (OUT/'semantic_audit_summary.json').write_text(json.dumps(result,indent=2)+'\n'); print(json.dumps(result,indent=2))
if __name__=='__main__': main()
