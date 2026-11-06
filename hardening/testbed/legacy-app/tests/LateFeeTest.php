<?php
// REQ-FEE-001: 2 percent fee after 30 days
function test_fee_after_30_days() { assert(late_fee(100.00, 31) === 2.00); }
function test_negative_days_rejected() { try { late_fee(1.0, -1); assert(false); } catch (InvalidArgumentException $e) {} }
// REQ-FEE-002: no fee up to 30 days
function test_no_fee_at_30_days() { assert(late_fee(100.00, 30) === 0.0); }
