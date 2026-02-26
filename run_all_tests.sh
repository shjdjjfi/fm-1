#!/usr/bin/env bash

mkdir -p proofs

echo "= Running Successful Automatic Proofs"
echo "== Running Paper Examples"
echo ""
echo "=== Example 1"
docker run -it --name example1 derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example1.proof examples/paper/example1.key
docker cp example1:/home/fm26/example1.proof proofs/
docker rm -f example1
echo ""
echo "=== Example 2"
docker run -it --name example2 derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example2.proof examples/paper/example2.key
docker cp example2:/home/fm26/example2.proof proofs/
docker rm -f example2
echo ""
echo "=== Example 3"
docker run -it --name example3 derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example3.proof examples/paper/example3.key
docker cp example3:/home/fm26/example3.proof proofs/
docker rm -f example3
echo ""
echo "=== Example 4"
docker run -it --name example4 derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example4.proof examples/paper/example4.key
docker cp example4:/home/fm26/example4.proof proofs/
docker rm -f example4
echo ""
echo "=== Example 9"
docker run -it --name example9 derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example9.proof examples/paper/example9.key
docker cp example9:/home/fm26/example9.proof proofs/
docker rm -f example9
echo ""
echo "=== Example 10"
docker run -it --name example10 derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example10.proof -m 12000 examples/paper/example10.key
docker cp example10:/home/fm26/example10.proof proofs/
docker rm -f example10
echo ""
echo "== Running Binary Search ="
docker run -it --name bin-search derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o binary-search.proof examples/binary-search/binary-search.key
docker cp bin-search:/home/fm26/binary-search.proof proofs/
docker rm -f bin-search
echo ""
echo "= Running Unsuccessful Automatic Proof"
echo "== Example 4 (Not closable due to possible integer overflow)"
docker run -it --rm derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar -s -o example4-overflow.proof examples/paper/example4-overflow.key
echo ""
echo "= Loading and Checking Manual Proofs"
echo "== Example 5 (Load completed proof)"
docker run -it --rm derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar --no-prove examples/paper/example5.proof
echo ""
echo "== Example 6 (Load completed proof)"
docker run -it --rm derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar --no-prove examples/paper/example6.proof
echo ""
echo "== Examples 7 & 8 (Load completed proof)"
docker run -it --rm derdrodt/fm26 java -jar rusty-key-0.1.0-exe.jar --no-prove examples/paper/example7-and-8.proof

