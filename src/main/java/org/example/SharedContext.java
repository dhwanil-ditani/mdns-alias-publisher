package org.example;

import java.net.DatagramPacket;
import java.net.MulticastSocket;
import java.util.concurrent.BlockingQueue;
import java.util.concurrent.LinkedBlockingQueue;

public class SharedContext {
    public volatile boolean running = true;
    public MulticastSocket socket;
    public final BlockingQueue<DatagramPacket> queue = new LinkedBlockingQueue<>();
}