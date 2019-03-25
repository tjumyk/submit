export function printDuration(totalSeconds: number): string {
  totalSeconds = Math.round(totalSeconds); // remove sub-second
  let output = '';
  let skipUnit = true;

  let units = ['h', 'm'];
  let unitSeconds = [3600, 60];
  for (let i = 0; i < units.length; ++i) {
    let tmp = unitSeconds[i];
    let value = Math.floor(totalSeconds / tmp);
    if (value || !skipUnit) {
      output += value + units[i];
      skipUnit = false;
    }
    totalSeconds %= tmp;
  }
  output += totalSeconds + 's';
  return output
}
