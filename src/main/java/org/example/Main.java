package org.example;

import java.io.IOException;
import java.net.*;

public class Main {
    public static void main(String[] args) {
        Thread listenerThread;
        Thread responderThread;
        SharedContext context = new SharedContext();

        try {
            context.socket = getSocket();

            MDNSListener listener = new MDNSListener(context);
            MDNSResponder responder = new MDNSResponder(context);

            listenerThread = new Thread(listener);
            responderThread = new Thread(responder);

            listenerThread.start();
            responderThread.start();

            listenerThread.join();
            responderThread.join();
        } catch (IOException |  InterruptedException e) {
            System.err.println(e.getMessage());
        } finally {
            if (context.socket != null && !context.socket.isClosed()) socket.close();
        }
    }

    private static MulticastSocket getSocket() throws IOException {
        MulticastSocket socket = new MulticastSocket(Constants.MDNS_PORT);
        InetSocketAddress multicastSocketAddress = new InetSocketAddress(Constants.MDNS_ADDRESS, Constants.MDNS_PORT);
        socket.joinGroup(multicastSocketAddress, getInternetFacingInterface());
        return socket;
    }


    private static NetworkInterface getInternetFacingInterface() throws IOException {
        InetAddress externalAddress = InetAddress.getByName("8.8.8.8");
        int dummyPort = 53;

        DatagramSocket socket = new DatagramSocket();
        socket.connect(externalAddress, dummyPort);
        InetAddress localAddress = socket.getLocalAddress();
        socket.close();

        return NetworkInterface.getByInetAddress(localAddress);
    }
}