FROM ubuntu:25.10

RUN groupadd -r fm26 && useradd -m -r -g fm26 fm26

# Install dependencies
RUN apt-get update && apt-get upgrade -y && apt-get install -y curl build-essential openjdk-21-jre-headless
RUN apt-get clean

USER fm26
ENV ARTIFACT_ROOT=/home/fm26
WORKDIR $ARTIFACT_ROOT

# Install Rust
RUN curl https://sh.rustup.rs -sSf | bash -s -- -y
RUN echo 'source $HOME/.cargo/env' >> /home/fm26/.bashrc
ENV PATH="/home/fm26/.cargo/bin:${PATH}"

# RustyKeY dependencies
COPY --chown=fm26:fm26 rustc-wrapper rustc-wrapper
RUN cd rustc-wrapper/wrapper && cargo install --path crates/cargo-key

COPY rusty-key-0.1.0-exe.jar /home/fm26
COPY --chown=fm26:fm26 examples examples
