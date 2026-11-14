const fs = require("fs");

function solution(numbers) {
  return numbers.reduce((sum, value) => sum + value, 0);
}

const input = fs.readFileSync(0, "utf8");
if (input.trim()) {
  const args = JSON.parse(input);
  console.log(JSON.stringify(solution(...args)));
}

module.exports = { solution };
