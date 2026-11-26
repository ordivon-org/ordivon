// Failure-only test carrier. Not used by the production adapter.
let input="";for await(const c of process.stdin)input+=c;
const {rpID}=JSON.parse(input);
switch(rpID){
 case "hang.example": await new Promise(resolve=>setTimeout(resolve,10000));break;
 case "oversize.example": process.stdout.write("x".repeat(262145));break;
 case "bad.example": process.stdout.write('{"kind":"verified","counter":1,"extra":true}');break;
 case "exit.example": process.exitCode=3;break;
 default: throw new Error("unexpected fixture");
}
