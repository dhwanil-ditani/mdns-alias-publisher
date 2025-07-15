package org.example;

import org.xbill.DNS.Message;
import org.xbill.DNS.Record;
import org.xbill.DNS.Section;

import java.io.IOException;
import java.net.DatagramPacket;
import java.net.MulticastSocket;

public class MDNSListener implements Runnable {

    private final SharedContext context;

    MDNSListener(SharedContext context) {
        this.context = context;
    }

    @Override
    public void run() {
        System.out.println("MDNSListener started...");
        MulticastSocket socket = context.socket;

        while (context.running && !socket.isClosed()) {
            try {
                byte[] buffer = new byte[Constants.BUFFER_SIZE];
                DatagramPacket packet = new DatagramPacket(buffer, buffer.length);
                socket.receive(packet);

                byte[] data = packet.getData();

                // Parse raw DNS message
                Message dnsMessage = new Message(data);
                System.out.println("\n📨 Received DNS Message from " + packet.getAddress());
                System.out.println("Header: " + dnsMessage.getHeader());

                for (Record question : dnsMessage.getSection(Section.QUESTION)) {
                    System.out.println("🔎 Question: " + question);
                }

                for (Record answer : dnsMessage.getSection(Section.ANSWER)) {
                    System.out.println("✅ Answer: " + answer);
                }
            } catch (IOException e) {
                System.err.println(e.getMessage());
                break;
            }
        }

        System.out.println("MDNSListener stopped.");
    }
}
