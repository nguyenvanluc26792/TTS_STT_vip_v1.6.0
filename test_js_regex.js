const s = "thế, nhưng";
const replaced = s.replace(/(?<=[^\W\d_]),\s*(?=[^\W\d_""«])/g, ", -- ");
console.log("Original: " + s);
console.log("Replaced: " + replaced);
console.log("Matched: " + (s !== replaced));
