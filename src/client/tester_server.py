# -*- coding: utf-8 -*-
# filesystem and bloc device unit tests
# part 1: internal filesystem's functions.
# tested with python2 only

from constantes import *
from bloc_device import *
from minixfs import *
from bitarray import *
from tester_answers import *
import unittest
import os
import sys

# Test requirements :
# Attention tj repartir d'un fichier originale (add_entry/del_entry) laissent le
# filesystem dans un état incertain
#
# cp minixfs_lab1.img.org remote_minixfs_lab1.img && ./server 1234 remote_minixfs_lab1.img
#
#
# - bloc_device class : modeling a disk drive with the following methods
#   -  read_bloc, write_bloc
# - minix_superbloc class : a structure storing minix superblocs infos.
# - minix_inode class : a structure modeling a minix inode
# - minix_filesystem class : modeling minix filesystem class with the following methods:
#   - ialloc(), ifree(), balloc(), bfree()
#   - bmap(), lookup_entry(), namei()
#   - ialloc_bloc(), add_entry(), del_entry()
# - bitarray class : used to store and manipulated inode and zone bitmaps in memory
#   member ofs minix_filesystem class


# server = '129.194.185.187'  # p.ex a computer in A406
server = 'localhost'
port = 2000


class MinixTester(unittest.TestCase):

    # test if the content returned by read_bloc
    # is the one we expect.
    def test_1_bloc_device_read_bloc(self):
        self.disk = bloc_device_network(BLOCK_SIZE, server, port)
        bloc2 = self.disk.read_bloc(2)
        bloc5 = self.disk.read_bloc(5)
        bloc7 = self.disk.read_bloc(7)
        bloc24 = self.disk.read_bloc(24)
        self.assertEqual(bloc2, BLOC2)
        self.assertEqual(bloc5, BLOC5)
        self.assertEqual(bloc7, BLOC7)
        self.assertEqual(bloc24, BLOC24)
        self.disk.close_connection()

    # exchange bloc2 and bloc5 on the bloc device and test if the content
    # returned by read_bloc on it matches.
    def test_2_bloc_device_write_bloc(self):
        self.disk = bloc_device_network(BLOCK_SIZE, server, port)
        # read bloc2 and bloc5
        bloc2 = self.disk.read_bloc(2)
        bloc5 = self.disk.read_bloc(5)
        # swap them
        # bloc2, bloc5 = bloc5, bloc2
        # write them
        self.disk.write_bloc(5, bloc2)
        self.disk.write_bloc(2, bloc5)
        # read bloc2 and bloc5
        bloc2 = self.disk.read_bloc(2)
        bloc5 = self.disk.read_bloc(5)
        # check if they are effectively swapped
        self.assertEqual(bloc2, BLOC5)
        self.assertEqual(bloc5, BLOC2)
        # put them back in place
        self.disk.write_bloc(5, bloc2)
        self.disk.write_bloc(2, bloc5)
        # read bloc2 and bloc5
        bloc2 = self.disk.read_bloc(2)
        bloc5 = self.disk.read_bloc(5)
        self.disk.close_connection()
        self.assertEqual(bloc2, BLOC2)
        self.assertEqual(bloc5, BLOC5)

    # superbloc test : read it and check object values
    def test_3_super_bloc_read_super(self):
        self.disk = bloc_device_network(BLOCK_SIZE, server, port)
        sb = minix_superbloc(self.disk)
        self.disk.close_connection()

        self.assertEqual(sb.s_ninodes, 6848)
        self.assertEqual(sb.s_nzones, 20480)
        self.assertEqual(sb.s_imap_blocks, 1)
        self.assertEqual(sb.s_zmap_blocks, 3)
        self.assertEqual(sb.s_firstdatazone, 220)
        self.assertEqual(sb.s_max_size, 268966912)

    # inode and zone map tests
    # we need to copy the original as it was modified
    # when testing write_bloc
    def test_4_fs_inode_and_bloc_bitmaps(self):
        self.minixfs = minix_file_system(server, port)
        self.assertEqual(self.minixfs.inode_map, INODEBITMAP1)
        self.assertEqual(self.minixfs.zone_map, ZONEBITMAP1)
        del self.minixfs

    # inode list content test
    def test_5_fs_inode_list(self):
        self.minixfs = minix_file_system(server, port)
        self.assertEqual(self.minixfs.inodes_list, INODELIST)
        del self.minixfs

    # testing ialloc()/ifree()
    # calling ialloc()/ifree() several time and checking
    # the bitmask values after/or checking the number returned
    # by ialloc after ifree and balloc after bfree.
    def test_6_fs_ialloc_ifree(self):
        self.minixfs = minix_file_system(server, port)
        new_inode_num = self.minixfs.ialloc()
        self.assertEqual(new_inode_num, NEWNODE1)
        self.minixfs.ifree(123)
        new_inode_num = self.minixfs.ialloc()
        self.assertEqual(new_inode_num, NEWNODE2)
        new_inode_num = self.minixfs.ialloc()
        self.assertEqual(new_inode_num, NEWNODE3)
        del self.minixfs

    # testing balloc()/bfree()
    # same method as ialloc/ifree testing
    # balloc write on the filesystem as it initialize all bloc bytes to \0
    def test_7_fs_balloc_bfree(self):
        self.minixfs = minix_file_system(server, port)
        new_bloc_num = self.minixfs.balloc()
        self.assertEqual(new_bloc_num, NEWBLOC1)
        self.minixfs.bfree(123)
        new_bloc_num = self.minixfs.balloc()
        self.assertEqual(new_bloc_num, NEWBLOC2)
        new_bloc_num = self.minixfs.balloc()
        self.assertEqual(new_bloc_num, NEWBLOC3)
        del self.minixfs
        return True

    # testing bmap function : just check that some bmaped
    # blocs have the right numbers.
    def test_8_fs_bmap(self):
        self.minixfs = minix_file_system(server, port)
        # bmap of inode 167, an inode with triple indirects
        # containing linux-0.95.tgz. Get all blocs of the file
        # direct blocs
        dir_bmap_list = []
        for i in range(0, 7):
            bmap_bloc = self.minixfs.bmap(self.minixfs.inodes_list[167], i)
            dir_bmap_list.append(bmap_bloc)
        self.assertEqual(dir_bmap_list, DIRMAP)
        
        # indirect blocs
        indir_bmap_list = []
        for i in range(7, 512+7):
            bmap_bloc = self.minixfs.bmap(self.minixfs.inodes_list[167], i)
            indir_bmap_list.append(bmap_bloc)
        self.assertEqual(indir_bmap_list, INDIRMAP)
        
        # double indirect blocs
        dbl_indir_bmap_list = []
        for i in range(512+7, 1024):
            bmap_bloc = self.minixfs.bmap(self.minixfs.inodes_list[167], i)
            dbl_indir_bmap_list.append(bmap_bloc)
        self.assertEqual(dbl_indir_bmap_list, DBLINDIRMAP)
        del self.minixfs

    # testing lookup_entry function : give a known inode
    # number, and name, expect another inode number
    # do a few lookups
    def test_9_fs_lookup_entry(self):
        self.minixfs = minix_file_system(server, port)
        # lookup_entry, inode 798 ("/usr/src/ps-0.97"), lookup for ps.c
        inode = self.minixfs.lookup_entry(self.minixfs.inodes_list[798], "ps.c")
        self.assertEqual(inode, LOOKUPINODE1)
        # lookup_entry, inode 212 ("/usr/src/linux/fs/minix"), lookup for namei.c
        inode = self.minixfs.lookup_entry(self.minixfs.inodes_list[212], "namei.c")
        self.assertEqual(inode, LOOKUPINODE2)
        del self.minixfs

    # testing namei function. Test that a few paths return
    # the expected inode number.
    def test_a_fs_namei(self):
        self.minixfs = minix_file_system(server, port)
        paths = ["/usr/src/linux/fs/open.c", "/bin/bash", "/", "/usr/include/assert.h"]
        namedinodelist = []
        for p in paths:
            namedinode = self.minixfs.namei(p)
            namedinodelist.append(namedinode)
        self.assertEqual(namedinodelist, NAMEDINODES)
        del self.minixfs

    # testing i_add_bloc, i_alloc_bloc ?
    # function allocate a new bloc for a given file in the bloc list.
    # check its bloc list in the inode, before and after addition
    # check that bmap on the inode return the newly added bloc number
    # do one direct i_alloc and one indirect i_alloc.
    # we might need to get a fresh copy of the filesystem
    def test_b_fs_ialloc_bloc(self):
        self.minixfs = minix_file_system(server, port)
        dir_bmap_list = []
        for i in range(0, 7):
            bmap_bloc = self.minixfs.bmap(self.minixfs.inodes_list[56], i)
            dir_bmap_list.append(bmap_bloc)
        self.assertEqual(dir_bmap_list, IALLOC1)
    
        # ialloc bloc 2 and 3 on the inode
        self.minixfs.ialloc_bloc(self.minixfs.inodes_list[56], 2)
        self.minixfs.ialloc_bloc(self.minixfs.inodes_list[56], 3)
        # print bmap again
        dir_bmap_list = []
        for i in range(0, 7):
            bmap_bloc = self.minixfs.bmap(self.minixfs.inodes_list[56], i)
            dir_bmap_list.append(bmap_bloc)
        self.assertEqual(dir_bmap_list, IALLOC2)
        del self.minixfs

    # testing bloc contents and inode maps before and after add_entry
    def test_c_fs_addentry(self):
        self.minixfs = minix_file_system(server, port)
        self.assertEqual(self.minixfs.bmap(self.minixfs.inodes_list[1], 0), ROOTNODEBLOCNUM1)

        tmpbloc2 = self.minixfs.disk.read_bloc(self.minixfs.bmap(self.minixfs.inodes_list[1], 1))
        rootnodebloc = self.minixfs.disk.read_bloc(self.minixfs.bmap(self.minixfs.inodes_list[1], 0))
        self.assertEqual(rootnodebloc, ROOTNODEBLOC1)
        for i in range(1, 57):
            self.minixfs.add_entry(self.minixfs.inodes_list[1], "new_ent"+str(i), self.minixfs.ialloc())

        rootnodebloc = self.minixfs.disk.read_bloc(self.minixfs.bmap(self.minixfs.inodes_list[1], 0))
        self.assertEqual(rootnodebloc, ROOTNODEBLOC1MOD)
        
        # more complex modification : add enough entries so that a new bloc must be allocated
        # check that the next bloc is still 0
        self.assertEqual(self.minixfs.bmap(self.minixfs.inodes_list[1], 1), ROOTNODEBLOCNUM2)
        # add some more entries
        for i in range(57, 60):
            self.minixfs.add_entry(self.minixfs.inodes_list[1], "new_ent"+str(i), self.minixfs.ialloc())
        # check that new bloc has been allocated
        self.assertEqual(self.minixfs.bmap(self.minixfs.inodes_list[1], 1), ROOTNODEBLOCNUM2NEW)
        # check its contents
        rootnodebloc2 = self.minixfs.disk.read_bloc(self.minixfs.bmap(self.minixfs.inodes_list[1], 1))
        self.assertEqual(rootnodebloc2, ROOTNODEBLOC2MOD)
        # put the original block back and close
        self.minixfs.disk.write_bloc(self.minixfs.bmap(self.minixfs.inodes_list[1], 0), ROOTNODEBLOC1)
        self.minixfs.disk.write_bloc(self.minixfs.bmap(self.minixfs.inodes_list[1], 1), tmpbloc2)
        del self.minixfs

    # testing bloc contents and inode maps before and after del_entry
    def test_d_fs_delentry(self):
        nodenum = 798
        names_to_del = ["attime.c", "cmdline.c", "free", "free.c", "Makefile", "makelog", "ps", "ps.0", "ps.1", "ps.c",
                        "psdata.c", "psdata.h", "ps.h", "pwcache.c"]
        self.minixfs = minix_file_system(server, port)
        self.assertEqual(self.minixfs.bmap(self.minixfs.inodes_list[nodenum], 0), NODE798BLOCNUM1)
    
        nodebloc = self.minixfs.disk.read_bloc(self.minixfs.bmap(self.minixfs.inodes_list[nodenum], 0))
        self.assertEqual(nodebloc, NODE798BLOC1)

        for name in names_to_del:
            self.minixfs.del_entry(self.minixfs.inodes_list[nodenum], name)
        nodebloc = self.minixfs.disk.read_bloc(self.minixfs.bmap(self.minixfs.inodes_list[nodenum], 0))
        self.assertEqual(nodebloc, NODE798BLOC1MOD)
        # put the originale block back and close
        self.minixfs.disk.write_bloc(self.minixfs.bmap(self.minixfs.inodes_list[nodenum], 0), NODE798BLOC1)
        del self.minixfs

if __name__ == '__main__':
    unittest.main()
