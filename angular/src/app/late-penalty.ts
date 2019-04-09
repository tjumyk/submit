export class LatePenaltySegment {
  fromDay: number;
  toDay?: number;
  days?: number;
  penaltyPerDay: number;
}

export class LatePenalty {
  readonly segments: LatePenaltySegment[];

  constructor(segments: LatePenaltySegment[]) {
    this.segments = segments;
  }

  getPenalty(days: number): number{
    if(!this.segments || this.segments.length == 0)
      return null;
    let penalty = 0;
    let segmentIndex = 0;
    while(days && segmentIndex < this.segments.length){
      const segment = this.segments[segmentIndex++];
      if(segment.days == null || days <= segment.days){
        penalty += segment.penaltyPerDay * days;
        break;
      }
      penalty += segment.penaltyPerDay * segment.days;
      days -= segment.days;
    }
    penalty = Math.min(1.0, penalty);
    return penalty;
  }

  static parse(expression: string): LatePenalty {
    if (!expression)
      return null;
    expression = expression.trim();
    if (!expression)
      return null;

    const segments: LatePenaltySegment[] = [];

    const penalties: number[] = [];
    for (let part of expression.split(/\s+/)) {
      const num = parseFloat(part);
      if(isNaN(num) || num < 0){
        throw `Invalid item in late penalty list: ${part}`;
      }
      penalties.push(num)
    }
    if (penalties.length == 0) {
      return null;
    }

    let index: number = 0;
    let day: number = 1;
    let fromDay: number = 0;
    let lastPenalty: number = null;
    let samePenaltyDays: number = 0;
    let accumulativePenalty: number = 0.0;

    while (true) {
      const penalty = penalties[index];
      accumulativePenalty += penalty;

      if (lastPenalty === null) { // first penalty
        lastPenalty = penalty;
        fromDay = day;
        samePenaltyDays = 1;
      } else {
        if (penalty == lastPenalty) {
          ++samePenaltyDays;
        } else {
          segments.push({
            fromDay: fromDay,
            toDay: fromDay + samePenaltyDays - 1,
            days: samePenaltyDays,
            penaltyPerDay: lastPenalty
          });
          lastPenalty = penalty;
          fromDay = day;
          samePenaltyDays = 1;
        }
      }

      if (Math.abs(accumulativePenalty - 1.0) < 1.0e-6) {
        break;
      }

      if (accumulativePenalty > 1.0) { // fix last day
        if (samePenaltyDays > 1) {
          --samePenaltyDays;
          segments.push({
            fromDay: fromDay,
            toDay: fromDay + samePenaltyDays - 1,
            penaltyPerDay: lastPenalty,
            days: samePenaltyDays
          });
        }

        lastPenalty -= accumulativePenalty - 1.0;
        fromDay = day;
        samePenaltyDays = 1;
        accumulativePenalty = 1.0;
        break;
      }

      // accumulative penalty must be less than 1.0 here
      if (index < penalties.length - 1) {
        ++index;
      } else {
        // keep index at the last position after list exhausted
        if (penalty == 0) {
          break; // but if last penalty is 0, stop now to avoid infinite loop
        }
      }
      ++day;
    }

    // remaining days
    if (samePenaltyDays) {
      if (lastPenalty == 0) {
        segments.push({ // endless segment
          fromDay: fromDay,
          penaltyPerDay: lastPenalty
        });
      } else {
        segments.push({
          fromDay: fromDay,
          toDay: fromDay + samePenaltyDays - 1,
          days: samePenaltyDays,
          penaltyPerDay: lastPenalty
        });
      }
    }

    return new LatePenalty(segments)
  }
}
