# Steganography Bachelor Semester Project

## Abstract
In digital communication, protecting the content of messages is achieved through cryptography,
which encrypts information so that only authorized parties can read it. However, encryption
alone does not conceal the existence of the message, observers know that secret
information is being transmitted.

Steganography addresses this limitation by hiding messages within ordinary media, such
as images, making their existence practically undetectable. While steganography is naturally
limited in payload size and thus best suited for small communications, it provides a basic
yet original way to protect covert exchanges: if a message cannot be seen, it cannot be
attacked or decrypted. This project aims to explore this approach by combining image-based
steganography with modern cryptographic techniques.

The goal of this Bachelor Semester Project is to develop a Python-based tool that embeds
messages into images, concealing the existence of the hidden content within the host
media. The system will ask the user to provide an image, a plaintext message, and a password,
and will generate a modified image containing the hidden content.

The project will combine a steganographic embedding process (such as Least Significant
Bit or alternative approaches) with an additional encryption (e.g AES) layer applied to the
message before embedding. This encryption layer will ensure that, even if hidden data is
detected and extracted, the hidden message remains protected.

We will also evaluate how much the embedding and encryption processes alter the image,
how detectable and secure the hidden message may be, and what trade-offs exist
between security, payload size, and image quality.

In addition to the embedding software, a secondary rudimentary steganalysis tool may
be developed to simulate attack scenarios. This tool will attempt to detect the presence
of hidden messages and perform brute-force attempts against the encryption layer. This
component will serve to test the robustness of the system under malicious attacks.

### System workflow
- The sender provides an image, a plaintext message, and a password.
- The message is encrypted using cryptographic techniques.
- The encrypted message is embedded into the image in a way that minimizes detectability.
- The receiver provides the modified image and the correct password to extract and
  decrypt the hidden message.

### Investigation points
- Security properties of the chosen encryption scheme.
- Resistance of the steganographic method against basic steganalysis.
- Trade-offs between payload size, security, and image distortion.
- Implementation challenges and performance considerations.

## Flowchart
![Flowchart](.docs/BSP2_Flowchart.png)

## How to Run the Program

...
