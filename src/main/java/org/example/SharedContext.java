package org.example;

import java.net.MulticastSocket;

public class SharedContext {
    public volatile boolean running = true;
    public MulticastSocket socket;
}