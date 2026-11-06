<?php
// REQ-FEE-001, REQ-FEE-002
function late_fee(float $total, int $days_late): float {
    if ($days_late < 0) { throw new InvalidArgumentException('days_late < 0'); }
    return $days_late > 30 ? round($total * 0.02, 2) : 0.0;
}
