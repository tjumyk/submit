export function printDuration(seconds) {
  let output = '';
  let units = ['h', 'm', 's'];
  let unitSeconds = [3600, 60, 1];
  for (let i = 0; i < units.length; ++i) {
    let tmp = unitSeconds[i];
    let value = Math.floor(seconds / tmp);
    if (value)
      output += value + units[i];
    seconds = seconds % tmp;
  }
  return output
}
