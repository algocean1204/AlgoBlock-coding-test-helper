const fs = require("fs");

function main() {
  const lines = fs.readFileSync(0, "utf8").trim().split("\n");
  const count = Number(lines[0]);
  let total = 0;
  for (let index = 1; index <= count; index += 1) {
    total += Number(lines[index]);
  }
  console.log(total);
}

main();
