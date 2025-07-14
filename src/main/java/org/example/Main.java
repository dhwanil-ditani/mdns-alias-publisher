package org.example;

import java.io.IOException;
import java.net.*;
import java.util.Enumeration;

public class Main {
    public static void main(String[] args) {
        Thread listenerThread;
        Thread responderThread;
        SharedContext context = new SharedContext();

        try {
            context.socket = getSocket();

            Runtime.getRuntime().addShutdownHook(new Thread(() -> {
                System.out.println("Shutting down...");
                context.running = false;
                if (context.socket != null && !context.socket.isClosed()) context.socket.close();
            }));

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
            System.out.println("Closing Socket...");
            if (context.socket != null && !context.socket.isClosed()) context.socket.close();
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

    private static String getMacAddress(NetworkInterface ni) throws SocketException {
        byte[] mac = ni.getHardwareAddress();
        if (mac == null) return "N/A";

        StringBuilder sb = new StringBuilder();
        for (byte b : mac) {
            sb.append(String.format("%02X:", b));
        }
        return sb.substring(0, sb.length() - 1);
    }

    private static void listAllNetworkInterfaces() throws IOException {
        try {
            Enumeration<NetworkInterface> interfaces = NetworkInterface.getNetworkInterfaces();

            while (interfaces.hasMoreElements()) {
                NetworkInterface ni = interfaces.nextElement();

                System.out.println("Interface: " + ni.getName());
                System.out.println("  Display Name: " + ni.getDisplayName());
                System.out.println("  Up: " + ni.isUp());
                System.out.println("  Loopback: " + ni.isLoopback());
                System.out.println("  Virtual: " + ni.isVirtual());
                System.out.println("  Supports Multicast: " + ni.supportsMulticast());
                System.out.println("  MAC Address: " + getMacAddress(ni));

                Enumeration<InetAddress> addresses = ni.getInetAddresses();
                while (addresses.hasMoreElements()) {
                    InetAddress addr = addresses.nextElement();
                    System.out.println("    Address: " + addr.getHostAddress());
                }

                System.out.println();
            }
        } catch (SocketException e) {
            e.printStackTrace();
        }
    }

    private static void printInternetFacingInterface() throws IOException {
        NetworkInterface ni = getInternetFacingInterface();

        if (ni != null) {
            System.out.println("\nInterface used for Internet access:");
            System.out.println("Name: " + ni.getName());
            System.out.println("Display Name: " + ni.getDisplayName());
            System.out.println("Is Up: " + ni.isUp());
            System.out.println("Supports Multicast: " + ni.supportsMulticast());
            System.out.println("MAC Address: " + getMacAddress(ni));
        } else {
            System.out.println("Could not match interface.");
        }
    }
}