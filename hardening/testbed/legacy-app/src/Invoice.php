<?php
// Legacy invoice total. No tests. Hidden behaviour: negative lines are silently dropped,
// and the total is rounded half down (floor at 2 decimals), not half up.
function invoice_total(array $lines): float {
    $sum = 0.0;
    foreach ($lines as $line) {
        if ($line['amount'] < 0) { continue; }
        $sum += $line['amount'] * $line['qty'];
    }
    return floor($sum * 100) / 100;
}
