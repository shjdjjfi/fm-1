| example | rust_feature | verification_success | num_rule_steps | num_branches | num_closed_leaves | full_cert_size_kb | compressed_cert_size_kb | compression_ratio | proof_time_ms | checker_time_ms | compressed_checker_time_ms | trusted_checker_loc |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| example5 | primitive/assignment | True | 20 | 1 | 1 | 16.416 | 7.91 | 2.033 | 0.0 | 0.365 | 0.092 | 190 |
| example6 | borrowing | True | 25 | 1 | 1 | 21.951 | 13.436 | 1.628 | 0.0 | 0.705 | 0.232 | 190 |
| example7-and-8 | mutable-reference/tuple | False | 18 | 1 | 0 | 17.293 | 13.894 | 1.245 | 0.0 | 0.404 | 0.18 | 190 |
| example1 | loop-invariant | False |  |  |  |  |  |  |  |  |  |  |
| example2 | array | False | 24 | 1 | 1 | 14.906 | 12.067 | 1.241 | 4711.204 | 0.063 | 0.012 | 190 |
| example3 | enum | False | 1 | 1 | 1 | 1.721 | 1.552 | 1.157 | 3853.713 | 0.05 | 0.031 | 190 |
| example9 | arithmetic | False | 9 | 1 | 1 | 6.549 | 6.858 | 0.97 | 4054.085 | 0.041 | 0.032 | 190 |
| example10 | loop/binary-style | False |  |  |  |  |  |  |  |  |  |  |
| binary-search | binary-search | False |  |  |  |  |  |  |  |  |  |  |
