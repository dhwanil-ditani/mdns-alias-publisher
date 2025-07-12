package org.example;

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
        System.out.println("MDNSListener started");

        MulticastSocket socket = context.socket;
        byte[] buffer = new byte[1024];
        DatagramPacket packet = new DatagramPacket(buffer, buffer.length);

        while (context.running && !socket.isClosed()) {

        }

        System.out.println("MDNSListener stopped.");
    }
}
