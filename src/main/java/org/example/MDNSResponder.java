package org.example;

import java.net.DatagramPacket;
import java.net.MulticastSocket;
import java.util.List;

public class MDNSResponder implements Runnable {

    private final SharedContext context;
    private List<String> aliases;

    MDNSResponder(SharedContext context) {
        this.context = context;
    }

    public void loadAliases() {

    }

    @Override
    public void run() {
        System.out.println("MDNSResponder started...");
        MulticastSocket socket = context.socket;

        while (context.running && !socket.isClosed()) {
            try {
                DatagramPacket packet = context.queue.take();
            } catch (InterruptedException e) {
                e.printStackTrace();
                break;
            }
        }

        System.out.println("MDNSResponder stopped.");
    }
}
