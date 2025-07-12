package org.example;

import java.io.IOException;
import java.net.MulticastSocket;

public class MDNSResponder implements Runnable {

    private final SharedContext context;

    MDNSResponder(SharedContext context) {
        this.context = context;
    }

    @Override
    public void run() {
        System.out.println("Hello from MDNSResponder!!");
        MulticastSocket socket = context.socket;

        while (context.running && !socket.isClosed()) {

        }

        System.out.println("MDNSResponder stopped.");
    }
}
